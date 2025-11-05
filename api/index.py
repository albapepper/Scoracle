import os
import sys
from pathlib import Path

# Ensure backend package is importable when running on Vercel
_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
	# Use tab indentation to match repo style if used elsewhere
	sys.path.insert(0, str(_BACKEND_DIR))

# Hint to code that we're on Vercel
os.environ.setdefault("VERCEL", "1")

# Import the FastAPI app
from app.main import app as fastapi_app  # type: ignore

# Vercel expects a module-level `app` (WSGI/ASGI) export
app = fastapi_app
