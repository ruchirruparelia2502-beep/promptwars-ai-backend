from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import health, ai

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="⚡ Production & Hackathon Ready AI Backend for PromptWars x Cynergy with Instant Cloud Deployment Support (Render, Railway, Fly.io, Vercel, Docker).",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Hacker-friendly CORS: allows any frontend (React, Next.js, Vue, Streamlit, Mobile) to connect seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(ai.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
