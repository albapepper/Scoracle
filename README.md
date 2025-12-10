# Scoracle – Sports News & Statistics Platform

A modern web app for sports news and statistics across NBA, NFL, and Football (soccer).

## ✨ Features

- **Multi-Sport Support** – NBA, NFL, Football with unified API
- **Fast Search** – In-memory autocomplete with fuzzy matching
- **News Aggregation** – Google News RSS pipeline
- **Dark/Light Mode** – System-aware theming
- **i18n** – English, Spanish, German, Portuguese, Italian

## 🗂 Project Structure

```
scoracle/
├── backend/                 # FastAPI (Python)
│   ├── app/
│   │   ├── main.py         # App entry point
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   └── database/       # SQLite helpers
│   └── instance/localdb/   # SQLite data files
│
├── scoracle-svelte/         # SvelteKit frontend
│   ├── src/
│   │   ├── routes/         # Pages (file-based routing)
│   │   └── lib/            # Components, stores, utilities
│   └── static/data/        # Bundled JSON for autocomplete
│
├── api/index.py            # Vercel serverless entry
├── local.ps1               # Local dev helper (Windows)
└── vercel.json             # Deployment config
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (or Bun for faster builds)

### Local Development

```powershell
# Backend only (FastAPI on :8000)
./local.ps1 backend

# Frontend only (Svelte on :5173)
./local.ps1 frontend

# Both
./local.ps1 up
```

Or run the frontend directly:

```powershell
cd scoracle-svelte
bun install    # or: npm install
bun run dev    # or: npm run dev
```

### API Docs

http://localhost:8000/api/docs

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `API_SPORTS_KEY` | API-Sports provider key |

## 📤 Deployment (Vercel)

1. Connect repo to Vercel
2. Set Root Directory: (leave empty)
3. Add environment variable: `API_SPORTS_KEY`
4. Deploy

The app auto-configures:
- Frontend: SvelteKit static build
- Backend: Python serverless function at `/api`

## 📄 License

MIT
