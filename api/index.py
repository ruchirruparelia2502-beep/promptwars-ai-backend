import os
import sys
import traceback
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Prepend project root directory to sys.path for Vercel serverless execution
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Ensure serverless runtime flag is set
os.environ.setdefault("VERCEL", "1")

# Top-level FastAPI assignment recognized by Vercel's @vercel/python static AST builder
app = FastAPI(title="LabLink Platform")

try:
    from app.main import app as _main_app
    app = _main_app
except Exception as _exc:
    _tb_lines = traceback.format_exc().splitlines()
    _err_msg = str(_exc)

    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    async def startup_error_diagnostic(path_name: str = ""):
        return JSONResponse(
            status_code=500,
            content={
                "error": "STARTUP_EXCEPTION",
                "exception": _err_msg,
                "traceback": _tb_lines,
            },
        )
