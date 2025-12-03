# How to Check Vercel Function Logs (CRITICAL)

The function is crashing with a 500 error. We **MUST** check the logs to see why.

## Step-by-Step Instructions:

### Method 1: Vercel Dashboard (Easiest)

1. **Go to your Vercel project**:
   - Visit: https://vercel.com/your-username/projects/scoracle
   - Or: https://vercel.com/dashboard

2. **Click on the latest deployment** (the one that's failing)

3. **Click "Functions" tab** (at the top)

4. **Click on `/api/index.py`** in the list

5. **Click "Logs" tab** (or scroll down to see logs)

6. **Look for**:
   - Red error messages
   - Python tracebacks
   - "ERROR importing app"
   - "ERROR with Mangum"
   - Any exception messages

### Method 2: Vercel CLI

```powershell
# Get your deployment URL from the dashboard, then:
vercel logs <your-deployment-url>

# Or inspect a specific deployment:
vercel inspect <deployment-url> --logs
```

### Method 3: Real-Time Logs

1. Open the logs in Vercel dashboard
2. In another tab, visit: `https://your-project.vercel.app/health`
3. Watch the logs update in real-time
4. You'll see exactly what error occurs

## What to Look For:

### Common Errors:

1. **Import Errors**:
   ```
   ModuleNotFoundError: No module named 'app'
   ImportError: cannot import name 'settings'
   ```
   → Fix: Check PYTHONPATH and file structure

2. **Missing Dependencies**:
   ```
   ModuleNotFoundError: No module named 'mangum'
   ```
   → Fix: Add to requirements.txt

3. **Environment Variable Errors**:
   ```
   KeyError: 'API_SPORTS_KEY'
   ```
   → Fix: Set env vars in Vercel dashboard

4. **File Not Found**:
   ```
   FileNotFoundError: instance/localdb/nba.sqlite
   ```
   → Fix: Check includeFiles in vercel.json

5. **Handler Format Errors**:
   ```
   TypeError: handler() missing required argument
   ```
   → Fix: Check Mangum handler format

## What to Share:

Once you check the logs, please share:
1. **The exact error message** (copy/paste)
2. **The full traceback** (if any)
3. **Any "ERROR" lines** from the logs
4. **The last few log lines** before the crash

This will tell us exactly what's wrong!

