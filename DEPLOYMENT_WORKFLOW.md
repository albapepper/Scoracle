# Vercel Deployment Workflow

## The Problem: Deploying Before Git Push

**If Vercel is connected to your Git repository**, it deploys from **Git**, not your local files!

This means:
- ❌ You make changes locally
- ❌ You run `vercel --prod` 
- ❌ Vercel deploys the **old version from Git** (not your local changes)
- ✅ Your changes aren't deployed!

## Two Deployment Methods

### Method 1: Git-Based Deployment (Auto-Deploy)
- Vercel watches your Git repository
- Automatically deploys when you push to `main` branch
- **Deploys from Git**, not local files
- Common setup for most projects

### Method 2: CLI Deployment (Manual)
- You run `vercel --prod` from command line
- **Deploys from local files** (current directory)
- Ignores Git connection
- Good for testing/debugging

## How to Check Which Method You're Using

1. **Check Vercel Dashboard**:
   - Go to: https://vercel.com/your-username/projects/scoracle
   - Click "Settings" → "Git"
   - If you see a connected repository = Git-based deployment

2. **Check CLI Output**:
   - When you run `vercel --prod`, does it say:
     - "Deploying from local files" = CLI deployment ✅
     - "Deploying from Git" = Git-based deployment ❌

## Recommended Workflow

### For Testing/Debugging (CLI):
```powershell
# 1. Make your changes
# 2. Deploy from local files (bypasses Git)
vercel --prod

# This deploys your LOCAL changes immediately
```

### For Production (Git-Based):
```powershell
# 1. Make your changes
# 2. Commit and push to Git
git add .
git commit -m "Fix backend deployment"
git push origin main

# 3. Vercel auto-deploys from Git
# (or manually trigger in dashboard)
```

## Current Situation

Since you've been deploying before pushing, you likely have:
- ✅ Local files with fixes
- ❌ Git repository with old code
- ❌ Vercel deploying old code from Git

## Solution

**Option 1: Deploy from Local (Quick Fix)**
```powershell
# Make sure you're using CLI deployment
vercel --prod

# This should deploy your LOCAL vercel.json and api/index.py
```

**Option 2: Push to Git First (Recommended)**
```powershell
# 1. Commit all your changes
git add vercel.json api/index.py requirements.txt runtime.txt
git commit -m "Fix Vercel backend deployment configuration"
git push origin main

# 2. Then deploy (or let Vercel auto-deploy)
vercel --prod
```

## Verify Your Deployment Source

After deploying, check the deployment details:
- Look at the "Source" field in Vercel dashboard
- It should show either:
  - "Git: main" (deploying from Git)
  - "CLI" (deploying from local)

## Best Practice

**Always push to Git before deploying** (unless you're explicitly testing locally):

```powershell
# 1. Make changes
# 2. Test locally: ./local.ps1 backend
# 3. Commit: git add . && git commit -m "Description"
# 4. Push: git push origin main
# 5. Deploy: vercel --prod (or let auto-deploy handle it)
```

This ensures:
- ✅ Your code is version controlled
- ✅ Vercel deploys the correct version
- ✅ You can rollback if needed
- ✅ Team members see the same code

