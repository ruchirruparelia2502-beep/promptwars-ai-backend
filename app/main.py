import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.routers import health, ai

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="⚡ Production & Hackathon Ready AI Backend for PromptWars x Cynergy with Instant Cloud Deployment Support (Render, Railway, Fly.io, Vercel, Docker).",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Hacker-friendly CORS: allows any frontend to connect seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health.router)
app.include_router(ai.router)

# Mount Static Files & Serve UI directly from FastAPI (Single-repo Hackathon Setup)
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", include_in_schema=False)
async def serve_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({
        "message": "PromptWars x Cynergy AI Backend is running",
        "docs": "/docs",
        "health": "/healthz"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

