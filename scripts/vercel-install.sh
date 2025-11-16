#!/bin/bash
# Install script for Vercel - installs frontend dependencies
# Note: Python dependencies are auto-installed by Vercel when it detects api/index.py

set -e

echo "Installing frontend dependencies..."
cd frontend && npm install --legacy-peer-deps
cd ..

