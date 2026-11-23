from fastapi import APIRouter
from app.config import settings
from app.schemas.models import HealthResponse
from app.services.gemini import gemini_service

router = APIRouter(tags=["System"])

@router.get("/", summary="Root endpoint")
async def root():
    return {
        "message": "Welcome to PromptWars x Cynergy AI Backend",
        "documentation": "/docs",
        "health": "/healthz",
        "version": settings.VERSION,
    }

@router.get("/healthz", response_model=HealthResponse, summary="Deployment Health Check")
async def health_check():
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        gemini_configured=gemini_service.is_configured(),
    )
