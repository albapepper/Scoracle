"""Vercel serverless function entrypoint for FastAPI app."""
import sys
import os
import json
import traceback

# CRITICAL: Define fallback handler FIRST before any imports that might fail
def emergency_fallback_handler(event, context):
    """Ultra-simple fallback that always works."""
    try:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "message": "Emergency fallback handler",
                "error": "Main handler failed to load",
                "python_version": sys.version,
                "cwd": os.getcwd()
            })
        }
    except:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "text/plain"},
            "body": "Emergency handler failed"
        }

# Initialize handler to fallback (will be replaced if imports succeed)
handler = emergency_fallback_handler

# CRITICAL: Print immediately to verify function is being called
try:
    print("=" * 80, file=sys.stderr)
    print("[api/index.py] MODULE LOADING STARTED", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
except:
    pass  # If even print fails, we're in deep trouble

# Diagnostic info collected during startup
STARTUP_DIAGNOSTICS = {
    "python_version": str(sys.version),
    "cwd": str(os.getcwd()),
    "errors": []
}

try:
    print("[api/index.py] Starting Python serverless function...", file=sys.stderr)
    print(f"[api/index.py] Python version: {sys.version}", file=sys.stderr)
    print(f"[api/index.py] Current directory: {os.getcwd()}", file=sys.stderr)
    print(f"[api/index.py] __file__: {__file__}", file=sys.stderr)
except Exception as e:
    print(f"[api/index.py] ERROR in initial print statements: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

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
        
        # Wrap handler to catch runtime errors
        original_handler = handler
        def wrapped_handler(event, context):
            try:
                print(f"[wrapped_handler] Event received: {event.get('path', 'unknown')}", file=sys.stderr)
                result = original_handler(event, context)
                print(f"[wrapped_handler] Handler completed successfully", file=sys.stderr)
                return result
            except Exception as e:
                import traceback
                print(f"[wrapped_handler] RUNTIME ERROR: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": "Runtime error in handler",
                        "message": str(e),
                        "traceback": traceback.format_exc()
                    }, indent=2)
                }
        handler = wrapped_handler
        print("[api/index.py] Handler wrapped with error catching", file=sys.stderr)
    else:
        print("[api/index.py] App is None, cannot create Mangum handler", file=sys.stderr)
except Exception as e:
    import traceback
    print(f"[api/index.py] ERROR with Mangum: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    STARTUP_DIAGNOSTICS["mangum_import"] = "failed"
    STARTUP_DIAGNOSTICS["errors"].append(f"mangum: {str(e)}")

# Fallback handler if main app failed to load
def fallback_handler(event, context):
    """Emergency fallback handler that returns diagnostic info."""
    import traceback
    print("[fallback_handler] Fallback handler invoked", file=sys.stderr)
    print(f"[fallback_handler] Event: {event}", file=sys.stderr)
    print(f"[fallback_handler] Context: {context}", file=sys.stderr)
    try:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Application failed to start",
                "diagnostics": STARTUP_DIAGNOSTICS,
                "import_error": IMPORT_ERROR,
                "handler_type": str(type(handler)) if 'handler' in globals() else "handler not defined",
            }, indent=2)
        }
    except Exception as e:
        print(f"[fallback_handler] ERROR in fallback: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Fallback handler failed: {str(e)}"}, indent=2)
        }

# Use the real handler if available, otherwise use fallback
if handler is None or handler == emergency_fallback_handler:
    if handler is None:
        print("[api/index.py] Handler is None, using fallback", file=sys.stderr)
        handler = fallback_handler
    else:
        print("[api/index.py] Using emergency fallback handler", file=sys.stderr)
        handler = emergency_fallback_handler

# CRITICAL: Ensure handler exists before export
if 'handler' not in globals() or handler is None:
    print("[api/index.py] WARNING: handler is None or not defined, using fallback", file=sys.stderr)
    handler = fallback_handler

# Export handler for Vercel
# Vercel Python runtime looks for a 'handler' variable at module level
# Mangum adapter wraps FastAPI app for AWS Lambda/Vercel compatibility
__all__ = ["handler"]

# Debug: Print handler type for troubleshooting
try:
    print(f"[api/index.py] Handler type: {type(handler)}", file=sys.stderr)
    print(f"[api/index.py] Handler is callable: {callable(handler)}", file=sys.stderr)
    print(f"[api/index.py] Handler module: {handler.__module__ if hasattr(handler, '__module__') else 'N/A'}", file=sys.stderr)
except Exception as e:
    print(f"[api/index.py] ERROR printing handler info: {e}", file=sys.stderr)

print("=" * 80, file=sys.stderr)
print("[api/index.py] MODULE LOADING COMPLETE", file=sys.stderr)
print("=" * 80, file=sys.stderr)

