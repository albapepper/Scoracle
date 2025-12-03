# Quick Fix for 404 Error

## The Problem
You're getting 404 errors even though the build succeeds. This usually means:
1. The handler isn't being found/called correctly
2. OR there's a runtime error that's being silently caught

## Immediate Steps

### 1. Make sure you're using backend-only config:

```powershell
# Check what config you're currently using
Get-Content vercel.json | Select-String "frontend"

# If it shows frontend, switch to backend-only:
Copy-Item vercel-backend-only.json vercel.json
```

### 2. Check Vercel Function Logs

This is the MOST IMPORTANT step. The logs will show you exactly what's happening:

1. Go to: https://vercel.com/your-username/projects/scoracle
2. Click on the latest deployment
3. Go to the "Functions" tab
4. Click on `api/index.py`
5. Check the "Logs" section

Look for:
- ✅ "Mangum handler created successfully" = Good!
- ❌ Import errors = Problem with dependencies or paths
- ❌ "Handler not found" = Problem with handler export
- ❌ Any Python exceptions = Shows the real error

### 3. Test with a Simple Endpoint

Try accessing these URLs (in order of simplicity):

```
https://your-project.vercel.app/health
https://your-project.vercel.app/
https://your-project.vercel.app/api/docs
```

### 4. If Still 404, Check These:

**A. Handler Export**
- Open `api/index.py`
- Make sure line 103 has: `__all__ = ["handler"]`
- Make sure `handler` variable exists (not None)

**B. Requirements**
- Make sure `requirements.txt` is at root
- Make sure `mangum>=0.17.0` is in requirements.txt

**C. Routes**
- Check `vercel.json` routes point to `/api/index.py`
- Make sure routes don't conflict

## Most Likely Causes

1. **Using wrong vercel.json** - Still has frontend build config
2. **Import error** - Check function logs for Python exceptions
3. **Handler not exported** - Verify `handler` variable exists at module level

## Next Steps After Checking Logs

Once you check the function logs, you'll see the actual error. Common fixes:

- **Import error**: Add missing dependency to requirements.txt
- **Path error**: Fix PYTHONPATH or includeFiles in vercel.json  
- **Handler not found**: Ensure handler is at module level and exported

