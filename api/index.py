import sys
import os
import traceback

# Add project root directory to sys.path for Vercel serverless execution
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Ensure serverless runtime flags are set
os.environ["VERCEL"] = "1"

try:
    from app.main import app
except Exception as e:
    tb = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    async def catch_startup_error(path_name: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "STARTUP_EXCEPTION",
                "exception": str(e),
                "traceback": tb.splitlines()
            }
        )

    @app.get("/")
    async def catch_startup_root():
        return JSONResponse(
            status_code=500,
            content={
                "error": "STARTUP_EXCEPTION",
                "exception": str(e),
                "traceback": tb.splitlines()
            }
        )
