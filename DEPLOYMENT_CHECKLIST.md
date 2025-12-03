# Deployment Checklist - Backend Only

## Step 1: Use Backend-Only Config

**CRITICAL**: Make sure you're using the backend-only configuration:

```powershell
# Backup current config
Copy-Item vercel.json vercel.json.backup

# Use backend-only config  
Copy-Item vercel-backend-only.json vercel.json

# Verify it worked
Get-Content vercel.json | Select-String "api/index.py"
```

## Step 2: Verify Files Are Present

- ✅ `requirements.txt` at root (copied from api/requirements.txt)
- ✅ `runtime.txt` at root (specifies Python version)
- ✅ `api/index.py` exists and exports `handler`
- ✅ `vercel.json` uses backend-only config

## Step 3: Deploy

```powershell
vercel --prod
```

## Step 4: Check Function Logs

After deployment, check the function logs to see what's happening:

```powershell
vercel inspect <your-deployment-url> --logs
```

Or visit: https://vercel.com/your-project/deployments

Look for:
- Import errors
- Handler creation messages
- Any Python exceptions

## Step 5: Test Endpoints

Try these URLs in order:

1. **Root endpoint**: `https://your-project.vercel.app/`
2. **Health check**: `https://your-project.vercel.app/health`
3. **API docs**: `https://your-project.vercel.app/api/docs`
4. **API root**: `https://your-project.vercel.app/api/v1/nba`

## Common Issues

### Still Getting 404?

1. **Check function logs** - Look for import errors or handler creation failures
2. **Verify handler is created** - Look for "Mangum handler created successfully" in logs
3. **Check routes** - Make sure routes in vercel.json match your API structure
4. **Test with simple endpoint** - Try `/health` first (simplest endpoint)

### Import Errors?

- Check that `backend/` directory is included in build
- Verify `PYTHONPATH` is set to `backend` in vercel.json
- Check that all dependencies are in requirements.txt

### Handler Not Found?

- Verify `handler` variable exists at module level in `api/index.py`
- Check that Mangum is installed (`mangum>=0.17.0` in requirements.txt)
- Look for "Handler type" and "Handler is callable" messages in logs

