"""Vercel serverless function entrypoint for FastAPI app."""
import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Import the FastAPI app
from app.main import app
from mangum import Mangum

# Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
handler = Mangum(app, lifespan="off")

