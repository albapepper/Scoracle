# Scoracle Svelte Frontend

A SvelteKit-based frontend for Scoracle, migrated from React.

## Features

- 🎨 **Dark/Light Mode** - Theme switching with system preference detection
- 🌍 **Internationalization** - Support for EN, ES, DE, PT, IT
- 🔍 **Fast Autocomplete** - In-memory fuzzy search on bundled JSON data
- ⚡ **SvelteKit** - File-based routing, SSR-ready
- 🎯 **Tailwind + Skeleton UI** - Utility-first styling with component library

## Getting Started

### Prerequisites

Choose one:
- **Node.js 18+** with npm 9+
- **Bun 1.0+** (recommended - much faster)

### Installation

#### Option A: Using Bun (Recommended)

```powershell
# Install Bun (Windows PowerShell)
powershell -c "irm bun.sh/install.ps1 | iex"

# Install dependencies (~5 seconds)
cd scoracle-svelte
bun install

# Copy static data files
copy ..\frontend\public\data\*.json static\data\
copy ..\frontend\public\scoracle-logo.png static\

# Start development server
bun run dev
```

#### Option B: Using npm

```powershell
cd scoracle-svelte

# Install dependencies (~60 seconds)
npm install

# Copy static data files
copy ..\frontend\public\data\*.json static\data\
copy ..\frontend\public\scoracle-logo.png static\

# Start development server
npm run dev
```

### Development Commands

| Command | npm | Bun |
|---------|-----|-----|
| Dev server | `npm run dev` | `bun run dev` |
| Type check | `npm run check` | `bun run check` |
| Tests | `npm run test` | `bun run test` |
| Build | `npm run build` | `bun run build` |
| Preview | `npm run preview` | `bun run preview` |

## Project Structure

```
src/
├── app.html              # HTML template
├── app.css               # Global styles
├── lib/
│   ├── components/       # Svelte components
│   ├── stores/           # Svelte stores (state management)
│   ├── data/             # Data fetching utilities
│   ├── i18n/             # Translations
│   └── utils/            # Utility functions
├── routes/               # File-based routing
│   ├── +layout.svelte    # Root layout
│   ├── +page.svelte      # Home page
│   ├── entity/           # Entity pages
│   └── mentions/         # Mentions pages
└── static/               # Static assets
    ├── data/             # Bundled JSON files
    └── scoracle-logo.png
```

## Deployment

### Vercel (Recommended)

The project is configured for Vercel deployment:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `/api` |

## Migration from React

This frontend was migrated from the React version located at `../frontend/`.

Key changes:
- React hooks → Svelte stores
- React Router → SvelteKit file-based routing
- Mantine UI → Tailwind + Skeleton UI
- i18next → svelte-i18n
- Context API → Svelte stores

## License

Private - All rights reserved.

