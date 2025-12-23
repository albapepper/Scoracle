# Scoracle Astro Frontend

A modern, performant Astro-based frontend for Scoracle - Sports News & Statistics Platform.

## 🚀 Features

- **Multi-Sport Support** – NBA, NFL, Football
- **Fast Search** – Autocomplete with fuzzy matching
- **Dark/Light Mode** – System-aware theming with manual toggle
- **Responsive Design** – Mobile-first, works on all devices
- **Server-Side Rendering** – Fast initial load with Astro
- **React Islands** – Interactive components using React
- **TypeScript** – Full type safety

## 📦 Tech Stack

- **Framework**: [Astro](https://astro.build/) - Modern static site builder
- **UI Framework**: [React](https://react.dev/) - For interactive components
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS
- **Icons**: [@tabler/icons-react](https://tabler-icons.io/)
- **Language**: TypeScript

## 🏗️ Project Structure

```
astro-frontend/
├── public/
│   └── data/              # Static JSON for autocomplete
├── src/
│   ├── components/        # React and Astro components
│   │   ├── Header.astro
│   │   ├── Footer.astro
│   │   ├── Widget.astro
│   │   ├── ThemeToggle.tsx
│   │   ├── SportSelector.tsx
│   │   └── SearchForm.tsx
│   ├── layouts/           # Page layouts
│   │   └── Layout.astro
│   ├── pages/             # File-based routing
│   │   ├── index.astro
│   │   ├── [sport]/
│   │   │   ├── player/[id].astro
│   │   │   └── team/[id].astro
│   │   └── 404.astro
│   ├── lib/
│   │   ├── api/           # API client and functions
│   │   ├── types/         # TypeScript type definitions
│   │   └── utils/         # Utility functions
│   └── styles/
│       └── global.css     # Global styles and Tailwind
├── astro.config.mjs
├── tailwind.config.mjs
└── tsconfig.json
```

## 🛠️ Development

### Prerequisites

- Node.js 18+ or Bun
- npm/bun/pnpm/yarn

### Install Dependencies

```bash
npm install
# or
bun install
```

### Start Dev Server

```bash
npm run dev
# or
bun run dev
```

The app will be available at `http://localhost:4321`

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## 🔌 API Integration

The frontend connects to the FastAPI backend at `/api/v1` by default. You can configure this with the `PUBLIC_API_URL` environment variable.

### Environment Variables

Create a `.env` file:

```env
PUBLIC_API_URL=/api/v1
```

## 📄 Routes

- `/` - Home page with sport selector and search
- `/[sport]/player/[id]` - Player detail page (e.g., `/nba/player/123`)
- `/[sport]/team/[id]` - Team detail page (e.g., `/nfl/team/456`)
- `/404` - Not found page

## 🎨 Theming

The app supports light, dark, and system themes. Users can toggle between them using the theme button in the header. The preference is saved in localStorage.

## 🔍 Search & Autocomplete

The search functionality uses static JSON files for autocomplete:
- Copy data files from `/frontend/public/data/`. (Legacy: `/scoracle-svelte/static/data/` if you have old artifacts.)
- Place them in `/public/data/`
- Files needed: `[sport]-players.json` and `[sport]-teams.json`

## 🚀 Deployment

### Vercel

The app is configured for Vercel deployment with the Node.js adapter:

1. Push to GitHub
2. Connect repo to Vercel
3. Vercel will auto-detect Astro and deploy

### Other Platforms

The app uses the Node.js adapter in standalone mode. Build and deploy:

```bash
npm run build
node dist/server/entry.mjs
```

## 📝 License

MIT
