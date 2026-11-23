"""
LabLink — GenAI-Powered Campus Laboratory Resource-Sharing Platform
FastAPI Application Entrypoint
PromptWars Hackathon (Google for Developers, Hack2Skill, Cynergy)
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.core.security import SecurityHeadersMiddleware
from app.routers import (
    health,
    ai,
    equipment,
    bookings,
    conflicts,
    approvals,
    analytics,
    copilot
)

app = FastAPI(
    title="LabLink — Campus Laboratory Resource Platform",
    version="2.0.0",
    description=(
        "⚡ GenAI-powered campus laboratory resource-sharing platform. "
        "Enables cross-department equipment discovery, O(1) bitmask slot booking, "
        "IRCTC/BookMyShow non-random conflict resolution with leased holds, "
        "and project-based faculty approvals with GenAI risk assessments."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# OWASP Hardened Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Universal CORS Middleware for frontend & API clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Core Platform Routers
app.include_router(health.router)
app.include_router(ai.router)
app.include_router(equipment.router)
app.include_router(bookings.router)
app.include_router(conflicts.router)
app.include_router(approvals.router)
app.include_router(analytics.router)
app.include_router(copilot.router)

# Mount Static UI Files (Accessible, Single-Repo Vercel Deployment)
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def serve_root():
    """Serves the accessible LabLink frontend or API descriptor."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({
        "message": "⚡ LabLink Platform is running",
        "documentation": "/docs",
        "health": "/healthz",
        "version": "2.0.0"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
