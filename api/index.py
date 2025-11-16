"""Vercel serverless function entrypoint for FastAPI app."""
import sys
import os

print("[api/index.py] Starting Python serverless function...", file=sys.stderr)
print(f"[api/index.py] Python version: {sys.version}", file=sys.stderr)
print(f"[api/index.py] Current directory: {os.getcwd()}", file=sys.stderr)
print(f"[api/index.py] __file__: {__file__}", file=sys.stderr)

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)
print(f"[api/index.py] Added to path: {backend_path}", file=sys.stderr)

# Basic diagnostics to ensure bundled assets exist in serverless env
try:
    backend_instance_dir = os.path.join(backend_path, "instance", "localdb")
    if os.path.isdir(backend_instance_dir):
        print(f"[api/index] backend/instance/localdb contents: {os.listdir(backend_instance_dir)}", file=sys.stderr)
    else:
        print(f"[api/index] backend/instance/localdb missing at {backend_instance_dir}", file=sys.stderr)
except Exception as diag_exc:
    print(f"[api/index] Failed to inspect localdb: {diag_exc}", file=sys.stderr)

# Import the FastAPI app
try:
    print("[api/index.py] Importing FastAPI app...", file=sys.stderr)
    from app.main import app
    from mangum import Mangum
    print("[api/index.py] FastAPI app imported successfully", file=sys.stderr)
except Exception as e:
    print(f"[api/index.py] ERROR importing app: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise

# Wrap FastAPI app with Mangum for AWS Lambda/Vercel compatibility
try:
    handler = Mangum(app, lifespan="off")
    print("[api/index.py] Mangum handler created successfully", file=sys.stderr)
except Exception as e:
    print(f"[api/index.py] ERROR creating handler: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    raise

