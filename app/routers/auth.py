"""
Authentication & Role Persona Router for LabLink
Permits perspective switching with cryptographically signed JWT bearer tokens
and role passcode verification (student, faculty, admin).
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.core.security import (
    CAMPUS_PERSONAS,
    ROLE_PASSCODES,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Roles"])


class LoginRequest(BaseModel):
    role: str = "student"
    passcode: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


@router.post("/token", summary="Dispense signed JWT for perspective switching")
def get_persona_token(
    role: str = Query(default="student", description="Perspective role: student, faculty, or admin"),
    passcode: Optional[str] = Query(default=None, description="Role passcode (required for faculty/admin)")
) -> Dict[str, Any]:
    role_key = role.lower().strip()
    if role_key not in CAMPUS_PERSONAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role '{role}'. Must be one of: student, faculty, admin."
        )

    # Protect elevated roles with passcode verification
    if role_key in ("faculty", "teacher"):
        expected = ROLE_PASSCODES["faculty"]
        if passcode != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Faculty authentication required. Please supply valid passcode (Demo Passcode: '{expected}')."
            )
    elif role_key in ("admin", "lab_admin"):
        expected = ROLE_PASSCODES["admin"]
        if passcode != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Admin authentication required. Please supply valid passcode (Demo Passcode: '{expected}')."
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


@router.post("/login", summary="Login with role credentials or college passcode")
def login(payload: LoginRequest) -> Dict[str, Any]:
    passcode = payload.passcode or payload.password
    return get_persona_token(role=payload.role, passcode=passcode)


@router.get("/me", summary="Inspect currently authenticated user identity")
def get_authenticated_profile(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "authenticated": True,
        "user": current_user
    }
