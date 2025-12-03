import os
import sys

# Add the backend directory to sys.path
# This is necessary because the Vercel build/runtime environment might not
# automatically add the backend directory to the Python path.
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.main import app

# Vercel looks for a variable named 'app' to serve as the entry point
# The 'app' variable imported from app.main is the FastAPI application instance
