# How to Check Vercel Function Logs

Since your function is deployed, we need to check the **runtime logs** (not build logs) to see what's happening when requests come in.

## Step-by-Step:

1. **Go to your Vercel deployment page**
   - Visit: https://vercel.com/your-username/projects/scoracle
   - Click on the latest deployment

2. **Open the Functions tab**
   - Click on "Functions" in the deployment view
   - You should see `/api/index.py` listed

3. **Click on `/api/index.py`**
   - This opens the function details

4. **Check the Logs section**
   - Look for runtime logs (not build logs)
   - These show what happens when someone visits your site

5. **Make a test request**
   - While viewing logs, try visiting: `https://your-project.vercel.app/health`
   - Watch the logs update in real-time

## What to Look For:

### ✅ Good Signs:
- "Starting Python serverless function..."
- "FastAPI app imported successfully"
- "Mangum handler created successfully"
- "Handler type: <class 'mangum.adapter.Mangum'>"
- "Handler is callable: True"

### ❌ Bad Signs:
- Import errors (ModuleNotFoundError, ImportError)
- "ERROR importing app"
- "ERROR with Mangum"
- "Using fallback handler due to import errors"
- Any Python tracebacks/exceptions

## Alternative: Use Vercel CLI

You can also check logs via command line:

```powershell
vercel logs <your-deployment-url>
```

Or inspect a specific deployment:

```powershell
vercel inspect <deployment-url> --logs
```

## What to Share:

Once you check the logs, please share:
1. Any error messages you see
2. Whether the handler is created successfully
3. What happens when you try to access `/health` endpoint

This will tell us exactly what's wrong!

