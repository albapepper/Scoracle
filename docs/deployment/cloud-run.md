# Deploying Scoracle to Google Cloud Run

This guide walks through publishing both the FastAPI backend and the React frontend on Google Cloud Run using Artifact Registry as the container source.

## 1. Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI (>= 466.0.0) and Docker installed locally
- Logged in with `gcloud auth login` and set the active project:  
  `gcloud config set project <PROJECT_ID>`
- Enable required services:
  ```bash
  gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    compute.googleapis.com
  ```

> Tip: Run `gcloud auth configure-docker` once so Docker can push to Artifact Registry.

## 2. Create Artifact Registry repositories

You can keep both images in a single repo or separate them. The examples below use one repo named `scoracle` in region `us-central1`—adjust to your preferred region.

```bash
gcloud artifacts repositories create scoracle \
  --repository-format=docker \
  --location=us-central1 \
  --description="Scoracle containers"
```

Define shell helpers for later steps:

```bash
export PROJECT_ID="<PROJECT_ID>"
export REGION="us-central1"
export REPO="scoracle"
export AR="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"
```

## 3. Build & push container images

### 3.1 Backend (FastAPI)

1. Build the image from the repo root:
   ```bash
   docker build -t ${AR}/backend:latest ./backend
   ```
2. Push the image:
   ```bash
   docker push ${AR}/backend:latest
   ```

### 3.2 Frontend (React static build)

The frontend embed its API base URL at build time. Build with the publicly accessible backend URL once it is known; for the initial build you can use a placeholder and redeploy after the backend is live.

```bash
export REACT_APP_API_BASE_URL="https://<BACKEND_URL>"  # update after backend deploy

docker build -t ${AR}/frontend:latest ./frontend

docker push ${AR}/frontend:latest
```

If you prefer to keep the image backend-agnostic, supply `REACT_APP_API_BASE_URL` as a build argument and fetch it dynamically with JavaScript at runtime instead of compile time.

## 4. Deploy to Cloud Run

### 4.1 Backend service

```bash
gcloud run deploy scoracle-backend \
  --image=${AR}/backend:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --port=8000 \
  --set-env-vars=BALLDONTLIE_API_KEY=<API_KEY> \
  --set-env-vars=BACKEND_CORS_ORIGINS=https://<FRONTEND_DOMAIN>,https://<FRONTEND_DEFAULT_URL>
```

Key notes:
- `BACKEND_CORS_ORIGINS` should include the eventual frontend URL (the default Cloud Run URL and any custom domain).
- Consider adding `--min-instances=0` for cost savings or `--min-instances=1` if you want to avoid cold starts.
- Secrets can be stored in Secret Manager and mounted with `--set-secrets` instead of inline values.

After deployment Cloud Run will print a service URL such as `https://scoracle-backend-abcdefg-uc.a.run.app`. Save this value—it becomes the frontend’s API base.

### 4.2 Frontend service

Rebuild (if needed) with the real backend URL and push again, then deploy:

```bash
docker build -t ${AR}/frontend:latest ./frontend \
  --build-arg REACT_APP_API_BASE_URL="https://scoracle-backend-abcdefg-uc.a.run.app"

docker push ${AR}/frontend:latest

gcloud run deploy scoracle-frontend \
  --image=${AR}/frontend:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --port=80
```

Because the frontend is served by Nginx as static files there are no runtime environment variables to set. After deployment you receive a URL similar to `https://scoracle-frontend-xyz.a.run.app`—use it immediately or map a custom domain.

## 5. (Optional) Custom domain & HTTPS

Cloud Run automatically provisions HTTPS certificates. To use your own domain:

```bash
gcloud run domain-mappings create --service=scoracle-frontend --domain=app.scoracle.com --region=${REGION}
```

Add the provided DNS records at your registrar. Repeat for the backend if you want a custom API domain.

## 6. CI/CD tips

- Store container images with version tags (e.g., `:v1`, `:git-sha`) to allow rollbacks: `docker build -t ${AR}/backend:$(git rev-parse --short HEAD)`.
- For automated deploys, configure Cloud Build triggers that build & push on commit, then run `gcloud run deploy` with the new tag.
- Monitor services via `gcloud run services describe` or the Cloud Console. Logs stream to Cloud Logging by default.

## 7. Cleanup

When done, remove services and repositories to avoid charges:

```bash
gcloud run services delete scoracle-frontend --region=${REGION}
gcloud run services delete scoracle-backend --region=${REGION}

gcloud artifacts repositories delete ${REPO} --location=${REGION}
```

That’s it! You now have Scoracle running on Cloud Run with independent frontend and backend services ready to scale with demand.
