import os
import sys

# Prepend project root directory to sys.path for Vercel serverless execution
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Ensure serverless runtime flag is set before importing app
os.environ.setdefault("VERCEL", "1")

# Top-level FastAPI ASGI entrypoint for @vercel/python
from app.main import app
