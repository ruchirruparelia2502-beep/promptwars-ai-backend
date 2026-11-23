import sys
import os

# Prepend project root directory to sys.path for Vercel serverless execution
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Ensure serverless runtime flags are set
os.environ["VERCEL"] = "1"

# Import FastAPI application
from app.main import app

# Top-level ASGI entrypoints recognized by Vercel and AWS Lambda
handler = app
application = app
