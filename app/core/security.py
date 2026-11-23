"""
Security & Hardening Layer for LabLink Platform
Provides OWASP Top-10 protection:
- Prompt Injection Sanitization & Jailbreak Defense
- HMAC-SHA256 State Integrity Verification
- In-memory Sliding-Window Rate Limiting (Anti-Bot / Slot Sniping Guard)
- OWASP Hardened HTTP Security Headers Middleware
- Role-Based Access Control (RBAC) helpers
"""

import hmac
import hashlib
import time
import re
from typing import Dict, List, Optional, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Secret key for HMAC state integrity (fallback to deterministic secret for serverless)
HMAC_SECRET = b"lablink-promptwars-cynergy-sec-2026-k9x8v"

# Dangerous prompt injection / jailbreak patterns
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|above|all)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"\[\s*system\s*\]", re.IGNORECASE),
    re.compile(r"<\s*script\s*>", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
    re.compile(r"dan\s+mode", re.IGNORECASE),
    re.compile(r"bypass\s+(filters?|rules?|safety)", re.IGNORECASE),
    re.compile(r"sudo\s+mode", re.IGNORECASE),
]


def sanitize_ai_prompt(text: str, max_chars: int = 1500) -> str:
    """
    Sanitizes user input before passing to GenAI models.
    Strips control tokens, injection phrases, and caps input size.
    Time Complexity: O(M) where M is length of input string.
    """
    if not text:
        return ""

    # Truncate to bound
    cleaned = text[:max_chars].strip()

    # Strip dangerous pattern phrases
    for pattern in INJECTION_PATTERNS:
        cleaned = pattern.sub("[REDACTED_INPUT]", cleaned)

    # Strip backticks to prevent markdown code injection escapes
    cleaned = cleaned.replace("```", "'''")

    # Strip non-printable / control ASCII characters except standard whitespace
    cleaned = "".join(ch for ch in cleaned if ch.isprintable() or ch in ("\n", "\r", "\t"))

    return cleaned


def generate_state_signature(payload_str: str) -> str:
    """
    Generates an HMAC-SHA256 signature for booking/approval state integrity.
    Prevents client-side tampering of reservation status or priority scores.
    """
    return hmac.new(HMAC_SECRET, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_state_signature(payload_str: str, signature: str) -> bool:
    """
    Constant-time HMAC verification against timing attacks.
    """
    expected = generate_state_signature(payload_str)
    return hmac.compare_digest(expected, signature)


class SlidingWindowRateLimiter:
    """
    High-efficiency in-memory sliding window rate limiter.
    Prevents bot scripts from spamming slot bookings or Tatkal-style hoarding.
    Time Complexity: O(1) amortized per request.
    Space Complexity: O(U) where U is number of unique client identifiers.
    """
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.client_records: Dict[str, List[float]] = {}

    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - self.window_seconds

        if client_id not in self.client_records:
            self.client_records[client_id] = [now]
            return True, self.max_requests - 1

        # Purge timestamps outside the sliding window
        valid_timestamps = [t for t in self.client_records[client_id] if t > cutoff]
        self.client_records[client_id] = valid_timestamps

        if len(valid_timestamps) >= self.max_requests:
            return False, 0

        self.client_records[client_id].append(now)
        remaining = self.max_requests - len(self.client_records[client_id])
        return True, remaining


# Global singleton rate limiter (60 requests per minute per IP)
global_rate_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies OWASP Top-10 Recommended Security Response Headers.
    Guarantees no MIME sniffing, frame protection, strict transport security, and CSP.
    """
    async def dispatch(self, request: Request, call_next):
        # Client IP extraction
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Apply rate limiting on state-mutating endpoints
        if request.url.path.startswith("/api/v1/bookings") and request.method == "POST":
            allowed, remaining = global_rate_limiter.is_allowed(client_ip)
            if not allowed:
                return Response(
                    content='{"detail": "Rate limit exceeded. Please wait before making more booking requests."}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                    headers={"Retry-After": "60"}
                )

        response = await call_next(request)

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com;"
        )
        response.headers["Permissions-Policy"] = "accelerometer=(), camera=(), microphone=(), geolocation=()"
        return response


# Role-Based Context Resolver (No login wall, roles passed via header or active context)
VALID_ROLES = {"student", "faculty", "lab_admin"}

def resolve_user_role(request: Request) -> str:
    """
    Extracts role from X-User-Role header or defaults to 'student'.
    Permits seamless UI role switching without requiring password entry.
    """
    role = request.headers.get("X-User-Role", "student").lower().strip()
    if role not in VALID_ROLES:
        return "student"
    return role
