import sys
import os

# Add parent directory to sys.path for Vercel serverless execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
