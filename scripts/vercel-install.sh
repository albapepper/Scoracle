#!/bin/bash
# Combined install script for Vercel - installs both frontend and Python dependencies

set -e

echo "Installing frontend dependencies..."
cd frontend && npm install --legacy-peer-deps

echo "Installing Python dependencies..."
cd ../api
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --target .python_packages
fi

cd ..

