#!/bin/bash
# Install script for Vercel - installs Svelte frontend dependencies
# Note: Python dependencies are auto-installed by Vercel when it detects api/index.py

set -e

echo "Installing Svelte frontend dependencies..."
cd scoracle-svelte && npm install
cd ..

