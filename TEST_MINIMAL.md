# Test with Minimal Handler

Since the function crashes immediately with no logs, let's test with a minimal handler first.

## Step 1: Temporarily Use Minimal Handler

```powershell
# Backup current handler
Copy-Item api/index.py api/index_full.py.backup

# Use minimal handler
Copy-Item api/index_minimal.py api/index.py

# Deploy
git add api/index.py
git commit -m "Test with minimal handler"
git push
vercel --prod
```

## Step 2: Test

Visit: `https://your-project.vercel.app/`

If this works, the issue is with imports/dependencies.
If this still crashes, the issue is with Vercel configuration.

## Step 3: Restore Full Handler

Once we know what works, we'll restore the full handler and fix imports one by one.

