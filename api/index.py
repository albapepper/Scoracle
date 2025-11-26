"""Vercel serverless function entrypoint for FastAPI app."""
import sys
import os
import json

# Diagnostic info collected during startup
STARTUP_DIAGNOSTICS = {
    "python_version": sys.version,
    "cwd": os.getcwd(),
    "errors": []
}

print("[api/index.py] Starting Python serverless function...", file=sys.stderr)
print(f"[api/index.py] Python version: {sys.version}", file=sys.stderr)
print(f"[api/index.py] Current directory: {os.getcwd()}", file=sys.stderr)
print(f"[api/index.py] __file__: {__file__}", file=sys.stderr)

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)
print(f"[api/index.py] Added to path: {backend_path}", file=sys.stderr)
STARTUP_DIAGNOSTICS["backend_path"] = backend_path

# Also try the /var/task path for Vercel serverless
vercel_backend_path = "/var/task/backend"
if os.path.isdir(vercel_backend_path) and vercel_backend_path not in sys.path:
    sys.path.insert(0, vercel_backend_path)
    print(f"[api/index.py] Added Vercel path: {vercel_backend_path}", file=sys.stderr)

# Basic diagnostics to ensure bundled assets exist in serverless env
try:
    backend_instance_dir = os.path.join(backend_path, "instance", "localdb")
    vercel_instance_dir = "/var/task/backend/instance/localdb"
    root_instance_dir = "/var/task/instance/localdb"
    
    for check_dir in [backend_instance_dir, vercel_instance_dir, root_instance_dir]:
        if os.path.isdir(check_dir):
            contents = os.listdir(check_dir)
            print(f"[api/index] {check_dir} contents: {contents}", file=sys.stderr)
            STARTUP_DIAGNOSTICS[f"dir_{check_dir}"] = contents
        else:
            print(f"[api/index] {check_dir} does not exist", file=sys.stderr)
            STARTUP_DIAGNOSTICS[f"dir_{check_dir}"] = "MISSING"
except Exception as diag_exc:
    print(f"[api/index] Failed to inspect localdb: {diag_exc}", file=sys.stderr)
    STARTUP_DIAGNOSTICS["errors"].append(f"localdb inspection: {diag_exc}")

# Try to import the FastAPI app
app = None
handler = None
IMPORT_ERROR = None

try:
    print("[api/index.py] Importing FastAPI app...", file=sys.stderr)
    from app.main import app as main_app
    app = main_app
    print("[api/index.py] FastAPI app imported successfully", file=sys.stderr)
    STARTUP_DIAGNOSTICS["app_import"] = "success"
except Exception as e:
    import traceback
    IMPORT_ERROR = traceback.format_exc()
    print(f"[api/index.py] ERROR importing app: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    STARTUP_DIAGNOSTICS["app_import"] = "failed"
    STARTUP_DIAGNOSTICS["errors"].append(f"app import: {str(e)}")

# Try to import Mangum
try:
    from mangum import Mangum
    STARTUP_DIAGNOSTICS["mangum_import"] = "success"
    if app is not None:
        handler = Mangum(app, lifespan="off")
        print("[api/index.py] Mangum handler created successfully", file=sys.stderr)
        STARTUP_DIAGNOSTICS["handler"] = "success"
except Exception as e:
    import traceback
    print(f"[api/index.py] ERROR with Mangum: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    STARTUP_DIAGNOSTICS["mangum_import"] = "failed"
    STARTUP_DIAGNOSTICS["errors"].append(f"mangum: {str(e)}")

# Fallback handler if main app failed to load
def fallback_handler(event, context):
    """Emergency fallback handler that returns diagnostic info."""
    return {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": "Application failed to start",
            "diagnostics": STARTUP_DIAGNOSTICS,
            "import_error": IMPORT_ERROR,
        }, indent=2)
    }

# Use the real handler if available, otherwise use fallback
if handler is None:
    print("[api/index.py] Using fallback handler due to import errors", file=sys.stderr)
    handler = fallback_handler

