from fastapi import APIRouter
from app.config import settings
from app.schemas.models import HealthResponse
from app.services.genai_engine import _get_api_key

router = APIRouter(tags=["System"])

@router.get("/healthz", response_model=HealthResponse, summary="Deployment Health Check")
async def health_check():
    key = _get_api_key()
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        gemini_configured=bool(key),
    )
