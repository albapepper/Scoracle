#!/bin/bash
# Combined build script for Vercel - builds Svelte frontend

set -e

echo "Building Svelte frontend..."
cd scoracle-svelte && npm run build

cd ..

