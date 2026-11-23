"""
Authentication & Role Persona Router for LabLink
Permits seamless perspective switching with cryptographically signed JWT bearer tokens.
Allows evaluator to switch between Student, Faculty, and Admin while strictly
enforcing server-side authorization on sensitive endpoints.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Dict, Any, Optional
from app.core.security import (
    CAMPUS_PERSONAS,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Roles"])


@router.post("/token", summary="Dispense signed JWT for perspective switching")
def get_persona_token(
    role: str = Query(default="student", description="Perspective role: student, faculty, or admin")
) -> Dict[str, Any]:
    role_key = role.lower().strip()
    if role_key not in CAMPUS_PERSONAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role '{role}'. Must be one of: student, faculty, admin."
        )

    persona = CAMPUS_PERSONAS[role_key]
    token = create_access_token(
        user_id=persona["sub"],
        role=persona["role"],
        name=persona["name"],
        academic_tier=persona.get("academic_tier", "capstone"),
        department=persona.get("department", "Engineering")
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": persona
    }


@router.get("/me", summary="Inspect currently authenticated user identity")
def get_authenticated_profile(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "authenticated": True,
        "user": current_user
    }
