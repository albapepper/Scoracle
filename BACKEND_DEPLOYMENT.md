# Backend-Only Deployment Guide

This guide explains how to deploy only the backend API to Vercel for debugging purposes.

## Quick Start

1. **Backup your current vercel.json**:
   ```powershell
   Copy-Item vercel.json vercel.json.backup
   ```

2. **Use the backend-only configuration**:
   ```powershell
   Copy-Item vercel-backend-only.json vercel.json
   ```

3. **Deploy to Vercel**:
   ```powershell
   vercel --prod
   ```
   Or use the Vercel dashboard to deploy.

4. **Restore original config when done**:
   ```powershell
   Copy-Item vercel.json.backup vercel.json
   ```

## What Changed

The `vercel-backend-only.json` configuration:
- ✅ Only builds the Python backend (`api/index.py`)
- ✅ Removes frontend build step
- ✅ Routes all requests to the API handler
- ✅ Includes backend code and SQLite databases

## Testing the Deployment

Once deployed, you can test:

1. **Health check**:
   ```
   https://your-project.vercel.app/health
   ```

2. **API root**:
   ```
   https://your-project.vercel.app/
   ```

3. **API docs**:
   ```
   https://your-project.vercel.app/api/docs
   ```

4. **Any API endpoint**:
   ```
   https://your-project.vercel.app/api/v1/nba/players/123
   ```

## Debugging Tips

1. **Check Vercel Function Logs**: Go to your Vercel dashboard → Functions → View logs

2. **Test endpoints individually**: Use the API docs at `/api/docs` to test each endpoint

3. **Check startup diagnostics**: The `api/index.py` includes diagnostic logging that will appear in Vercel logs

4. **Review API_ENDPOINTS.md**: Use this to identify unused endpoints that might be causing issues

## Common Issues

### 404 Errors / "No Framework Detected"
- **Requirements.txt location**: Vercel needs `requirements.txt` at the project root (now included)
- **Handler export**: Ensure `api/index.py` exports the handler (now fixed)
- **Runtime specification**: Added `runtime.txt` to specify Python version
- Check Vercel function logs: `vercel inspect <deployment-url> --logs`

### Import Errors
- Check that all dependencies are in `requirements.txt` (root) and `api/requirements.txt`
- Verify `PYTHONPATH` is set correctly in vercel.json
- Ensure `mangum` is in requirements.txt (needed for FastAPI → AWS Lambda adapter)

### Database Not Found
- Ensure `instance/localdb/` directory is included in the build
- Check that SQLite files are committed to git (they should be)

### Cold Start Timeouts
- Vercel serverless functions have a 10-second timeout on free tier
- Consider removing heavy imports or lazy-loading modules
- The `lifespan="off"` in Mangum helps avoid startup delays

## Restoring Full Deployment

When you're ready to deploy both frontend and backend again:

```powershell
Copy-Item vercel.json.backup vercel.json
vercel --prod
```

