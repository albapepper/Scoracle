#!/bin/bash
# Combined build script for Vercel - builds frontend

set -e

echo "Building frontend..."
cd frontend && npm run build

cd ..

