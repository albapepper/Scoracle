"""Vercel serverless function entrypoint for FastAPI app."""
import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Basic diagnostics to ensure bundled assets exist in serverless env
try:
    backend_instance_dir = os.path.join(backend_path, "instance", "localdb")
    if os.path.isdir(backend_instance_dir):
        print("[api/index] backend/instance/localdb contents:", os.listdir(backend_instance_dir))
    else:
        print("[api/index] backend/instance/localdb missing at", backend_instance_dir)
except Exception as diag_exc:
    print("[api/index] Failed to inspect localdb:", diag_exc)

# Import the FastAPI app
from app.main import app
from mangum import Mangum

# Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
handler = Mangum(app, lifespan="off")

