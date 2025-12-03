# Deploy Minimal Handler First

Since the function crashes immediately with no logs, let's test with the absolute simplest handler possible.

## Quick Test

1. **Temporarily replace api/index.py with minimal version:**

```powershell
# Backup current
Copy-Item api/index.py api/index_full.py.backup

# Use minimal
Copy-Item api/index_minimal.py api/index.py

# Deploy
git add api/index.py
git commit -m "Test minimal handler"
git push
vercel --prod
```

2. **Test the endpoint:**
   - Visit: `https://your-project.vercel.app/`
   - Should return: `{"message": "Minimal handler works!", ...}`

3. **If minimal works:**
   - The issue is with imports/dependencies
   - Restore full handler and fix imports one by one

4. **If minimal still crashes:**
   - The issue is with Vercel configuration
   - Check vercel.json routes and builds config

## Restore Full Handler

```powershell
Copy-Item api/index_full.py.backup api/index.py
```

