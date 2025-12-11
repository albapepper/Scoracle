# Scoracle Qwik Frontend - Comprehensive Development Plan

This document outlines the complete plan for building a new Qwik frontend for Scoracle using **Qwik UI** for theming and **TypeScript** as the primary language.

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Setup](#project-setup)
4. [Directory Structure](#directory-structure)
5. [TypeScript Configuration](#typescript-configuration)
6. [Theming with Qwik UI](#theming-with-qwik-ui)
7. [Routing Architecture](#routing-architecture)
8. [State Management](#state-management)
9. [Internationalization (i18n)](#internationalization-i18n)
10. [API Integration](#api-integration)
11. [Component Migration Plan](#component-migration-plan)
12. [Testing Strategy](#testing-strategy)
13. [Build & Deployment](#build--deployment)
14. [Development Phases](#development-phases)
15. [Best Practices & Guidelines](#best-practices--guidelines)

---

## Overview

### Current State

Scoracle currently uses **SvelteKit** for the frontend with:
- BeerCSS for styling
- svelte-i18n for internationalization (5 languages: en, es, de, pt, it)
- Svelte stores for state management
- File-based routing

### Target State

Build a modern, performant Qwik frontend that:
- Leverages Qwik's resumability for instant interactivity
- Uses Qwik UI components and theming system
- Maintains feature parity with the existing SvelteKit frontend
- Emphasizes TypeScript-first development
- Integrates seamlessly with the existing FastAPI backend

### Why Qwik?

- **Resumability**: Zero hydration overhead, instant interactivity
- **Lazy Loading**: Fine-grained lazy loading of components
- **TypeScript Native**: Built with TypeScript from the ground up
- **Performance**: Sub-second Time to Interactive (TTI)
- **Familiar Syntax**: JSX-like syntax familiar to React developers

---

## Technology Stack

### Core Framework

| Technology | Version | Purpose |
|-----------|---------|---------|
| Qwik | ^1.x (latest) | Core framework |
| Qwik City | ^1.x (latest) | Meta-framework (routing, SSR) |
| TypeScript | ^5.5+ | Primary language |
| Vite | ^5.x | Build tool |

### UI & Styling

| Technology | Purpose |
|-----------|---------|
| Qwik UI (Styled Kit) | Pre-built accessible components with theming |
| Tailwind CSS | Utility-first CSS (used by Qwik UI) |
| CSS Variables | Custom theming support |

### State & Data

| Technology | Purpose |
|-----------|---------|
| Qwik Signals | Reactive state management |
| useContext$ | Shared application state |
| routeLoader$ | Server-side data loading |
| routeAction$ | Server-side mutations |

### Testing & Quality

| Technology | Purpose |
|-----------|---------|
| Vitest | Unit testing |
| Playwright | E2E testing |
| ESLint | Code linting |
| Prettier | Code formatting |

---

## Project Setup

### 1. Initialize Project

\`\`\`bash
# Create new Qwik project with TypeScript
npm create qwik@latest scoracle-qwik

# Select options:
# - Empty App (for full control)
# - TypeScript: Yes
# - Package manager: npm (or bun)
\`\`\`

### 2. Install Dependencies

\`\`\`bash
cd scoracle-qwik

# Core Qwik UI (Styled Kit - includes Tailwind)
npm install @qwik-ui/styled

# Tailwind CSS (required by Qwik UI Styled)
npm install -D tailwindcss postcss autoprefixer

# Icons (replacement for @tabler/icons-svelte)
npm install qwik-feather-icons
# or use heroicons/lucide via qwik-icon

# i18n support
npm install @modular-forms/qwik  # optional: for forms
npm install qwik-speak  # i18n library for Qwik

# Development utilities
npm install -D @types/node
\`\`\`

### 3. Initialize Tailwind CSS

\`\`\`bash
npx tailwindcss init -p
\`\`\`

### 4. Configure Qwik UI

\`\`\`bash
# Initialize Qwik UI styled components
npx qwik-ui init
\`\`\`

---

## Directory Structure

\`\`\`
scoracle-qwik/
├── public/
│   ├── data/                    # Static JSON for autocomplete (migrate from Svelte)
│   │   ├── nba-players.json
│   │   ├── nba-teams.json
│   │   ├── nfl-players.json
│   │   ├── nfl-teams.json
│   │   ├── football-players.json
│   │   └── football-teams.json
│   └── favicon.ico
│
├── src/
│   ├── components/              # Reusable components
│   │   ├── header/
│   │   │   └── Header.tsx
│   │   ├── footer/
│   │   │   └── Footer.tsx
│   │   ├── search/
│   │   │   ├── SearchForm.tsx
│   │   │   └── EntityAutocomplete.tsx
│   │   ├── widgets/
│   │   │   └── Widget.tsx
│   │   └── ui/                  # Qwik UI component exports
│   │       └── index.ts
│   │
│   ├── routes/                  # Qwik City file-based routing
│   │   ├── index.tsx            # Home page (/)
│   │   ├── layout.tsx           # Root layout
│   │   ├── player/
│   │   │   └── [sport]/
│   │   │       └── [id]/
│   │   │           └── index.tsx
│   │   ├── team/
│   │   │   └── [sport]/
│   │   │       └── [id]/
│   │   │           └── index.tsx
│   │   ├── entity/
│   │   │   └── [type]/
│   │   │       └── [sport]/
│   │   │           └── [id]/
│   │   │               └── index.tsx
│   │   └── mentions/
│   │       └── [type]/
│   │           └── [sport]/
│   │               └── [id]/
│   │                   └── index.tsx
│   │
│   ├── integrations/            # Third-party integrations
│   │   └── qwik-ui/
│   │       └── index.ts
│   │
│   ├── lib/                     # Shared utilities
│   │   ├── api/
│   │   │   ├── client.ts        # API client configuration
│   │   │   ├── entities.ts      # Entity API calls
│   │   │   └── types.ts         # API types
│   │   ├── data/
│   │   │   └── loader.ts        # Static data loader
│   │   ├── i18n/
│   │   │   ├── index.ts
│   │   │   └── translations/
│   │   │       ├── en.json
│   │   │       ├── es.json
│   │   │       ├── de.json
│   │   │       ├── pt.json
│   │   │       └── it.json
│   │   ├── stores/
│   │   │   ├── sport.context.ts
│   │   │   ├── theme.context.ts
│   │   │   └── language.context.ts
│   │   └── utils/
│   │       ├── entityName.ts
│   │       └── index.ts
│   │
│   ├── entry.dev.tsx            # Dev entry
│   ├── entry.preview.tsx        # Preview entry
│   ├── entry.ssr.tsx            # SSR entry
│   ├── global.css               # Global styles + Tailwind
│   └── root.tsx                 # Root component
│
├── tests/
│   ├── unit/                    # Vitest unit tests
│   └── e2e/                     # Playwright E2E tests
│
├── .eslintrc.cjs
├── .prettierrc
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── vite.config.ts
└── vercel.json
\`\`\`

---

## TypeScript Configuration

### tsconfig.json

\`\`\`json
{
  "compilerOptions": {
    "allowJs": true,
    "target": "ES2021",
    "module": "ES2020",
    "lib": ["ES2021", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "jsxImportSource": "@builder.io/qwik",
    "strict": true,
    "noEmit": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "bundler",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "incremental": true,
    "isolatedModules": true,
    "outDir": "tmp",
    "paths": {
      "~/*": ["./src/*"]
    },
    "types": ["node", "vite/client"]
  },
  "files": [".eslintrc.cjs"],
  "include": ["src/**/*.ts", "src/**/*.tsx"]
}
\`\`\`

### TypeScript Best Practices for This Project

1. **Strict Mode**: Always enabled (\`"strict": true\`)
2. **Path Aliases**: Use \`~/\` for clean imports
3. **Type-First Development**: Define types before implementation
4. **No \`any\`**: Use \`unknown\` or proper generics instead
5. **Component Props**: Define explicit interfaces for all component props
6. **API Types**: Generate or maintain strict types for API responses

### Type Definitions

Create a dedicated types file (\`src/lib/api/types.ts\`):

\`\`\`typescript
// Entity Types
export type EntityType = 'player' | 'team';
export type SportId = 'nba' | 'nfl' | 'football';

export interface EntityInfo {
  id: string;
  name: string;
  type: EntityType;
  sport?: SportId;
}

export interface WidgetData {
  type: EntityType;
  display_name: string;
  subtitle?: string;
  photo_url?: string;
  logo_url?: string;
  position?: string;
  age?: number;
  height?: string;
  conference?: string;
  division?: string;
}

export interface NewsArticle {
  id: string;
  title: string;
  url: string;
  source: string;
  published_at: string;
  summary?: string;
  image_url?: string;
}

export interface EntityResponse {
  entity: EntityInfo;
  widget?: WidgetData;
  news?: NewsArticle[];
  enhanced?: Record<string, unknown>;
  stats?: Record<string, unknown>;
}

// Sport Configuration
export interface SportConfig {
  id: SportId;
  display: string;
  icon?: string;
}

export const SPORTS: readonly SportConfig[] = [
  { id: 'nba', display: 'NBA' },
  { id: 'nfl', display: 'NFL' },
  { id: 'football', display: 'Football' },
] as const;
\`\`\`

---

## Theming with Qwik UI

### Overview

Qwik UI provides two kits:
- **Headless Kit**: Unstyled, fully accessible components
- **Styled Kit**: Pre-styled with Tailwind CSS + theming

We will use the **Styled Kit** for faster development and consistent theming.

### Theme Configuration

\`\`\`typescript
// tailwind.config.js
import { qwikUi } from '@qwik-ui/styled/tailwind';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './node_modules/@qwik-ui/styled/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Custom Scoracle brand colors
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',  // Main primary
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        // Sport-specific accent colors
        nba: {
          primary: '#1d428a',    // NBA blue
          secondary: '#c8102e',  // NBA red
        },
        nfl: {
          primary: '#013369',    // NFL blue
          secondary: '#d50a0a',  // NFL red
        },
        football: {
          primary: '#326b3f',    // Soccer green
          secondary: '#ffffff',
        },
      },
    },
  },
  plugins: [qwikUi()],
};
\`\`\`

### Theme Context

\`\`\`typescript
// src/lib/stores/theme.context.ts
import { 
  createContextId, 
  useContext, 
  useContextProvider,
  useSignal,
  useVisibleTask$,
  type Signal
} from '@builder.io/qwik';

export type ColorScheme = 'light' | 'dark' | 'system';

export interface ThemeContext {
  colorScheme: Signal<ColorScheme>;
  effectiveScheme: Signal<'light' | 'dark'>;
  toggle: () => void;
  setScheme: (scheme: ColorScheme) => void;
}

export const ThemeContextId = createContextId<ThemeContext>('theme-context');

export function useTheme(): ThemeContext {
  return useContext(ThemeContextId);
}

export function useThemeProvider() {
  const colorScheme = useSignal<ColorScheme>('system');
  const effectiveScheme = useSignal<'light' | 'dark'>('light');

  useVisibleTask$(({ track }) => {
    track(() => colorScheme.value);

    // Read from localStorage on mount
    const saved = localStorage.getItem('color-scheme') as ColorScheme | null;
    if (saved && ['light', 'dark', 'system'].includes(saved)) {
      colorScheme.value = saved;
    }

    // Apply theme
    const applyTheme = () => {
      let effective: 'light' | 'dark';
      
      if (colorScheme.value === 'system') {
        effective = window.matchMedia('(prefers-color-scheme: dark)').matches 
          ? 'dark' 
          : 'light';
      } else {
        effective = colorScheme.value;
      }

      effectiveScheme.value = effective;
      document.documentElement.classList.toggle('dark', effective === 'dark');
      localStorage.setItem('color-scheme', colorScheme.value);
    };

    applyTheme();

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', applyTheme);

    return () => mediaQuery.removeEventListener('change', applyTheme);
  });

  const context: ThemeContext = {
    colorScheme,
    effectiveScheme,
    toggle: () => {
      const schemes: ColorScheme[] = ['light', 'dark', 'system'];
      const currentIndex = schemes.indexOf(colorScheme.value);
      colorScheme.value = schemes[(currentIndex + 1) % schemes.length];
    },
    setScheme: (scheme: ColorScheme) => {
      colorScheme.value = scheme;
    },
  };

  useContextProvider(ThemeContextId, context);

  return context;
}
\`\`\`

### Qwik UI Components to Use

| Component | Use Case |
|-----------|----------|
| Button | Sport selector, actions |
| Card | Widget display, news cards |
| Input | Search input |
| Combobox | Entity autocomplete |
| Select | Language selector |
| Tabs | Navigation tabs |
| Modal | Settings, dialogs |
| Toast | Notifications |
| Skeleton | Loading states |

---

## Routing Architecture

### File-Based Routing with Qwik City

\`\`\`
Routes Structure:
/                           → Home page (sport selector + search)
/player/[sport]/[id]        → Player detail page
/team/[sport]/[id]          → Team detail page
/entity/[type]/[sport]/[id] → Generic entity page
/mentions/[type]/[sport]/[id] → News mentions page
\`\`\`

### Example Route Implementation

\`\`\`typescript
// src/routes/player/[sport]/[id]/index.tsx
import { component$ } from '@builder.io/qwik';
import { routeLoader$, type DocumentHead } from '@builder.io/qwik-city';
import { getEntity, type EntityResponse } from '~/lib/api/entities';
import { Widget } from '~/components/widgets/Widget';

export const usePlayerData = routeLoader$(async ({ params, fail }) => {
  const { sport, id } = params;
  
  try {
    const data = await getEntity('player', id, sport, {
      includeWidget: true,
      includeNews: true,
    });
    return data;
  } catch (error) {
    throw fail(404, {
      message: \`Player not found: \${id}\`,
    });
  }
});

export default component$(() => {
  const playerData = usePlayerData();

  return (
    <div class="container mx-auto p-4">
      {playerData.value.widget && (
        <Widget data={playerData.value.widget} />
      )}
      
      {/* News section */}
      <section class="mt-8">
        <h2 class="text-2xl font-bold mb-4">Latest News</h2>
        {playerData.value.news?.map((article) => (
          <article key={article.id} class="card mb-4">
            <h3>{article.title}</h3>
            <p>{article.summary}</p>
          </article>
        ))}
      </section>
    </div>
  );
});

export const head: DocumentHead = ({ resolveValue }) => {
  const data = resolveValue(usePlayerData);
  return {
    title: \`\${data.entity.name} - Scoracle\`,
    meta: [
      {
        name: 'description',
        content: \`Stats and news for \${data.entity.name}\`,
      },
    ],
  };
};
\`\`\`

---

## State Management

### Context-Based State with Signals

Qwik uses **Signals** for reactive state and **Context** for shared state.

\`\`\`typescript
// src/lib/stores/sport.context.ts
import { 
  createContextId, 
  useContext, 
  useContextProvider,
  useSignal,
  useVisibleTask$,
  type Signal
} from '@builder.io/qwik';
import { type SportId, SPORTS, type SportConfig } from '~/lib/api/types';

export interface SportContext {
  activeSport: Signal<SportId>;
  sports: readonly SportConfig[];
  change: (sportId: SportId) => void;
}

export const SportContextId = createContextId<SportContext>('sport-context');

export function useSport(): SportContext {
  return useContext(SportContextId);
}

export function useSportProvider() {
  const activeSport = useSignal<SportId>('nba');

  useVisibleTask$(() => {
    // Restore from localStorage
    const saved = localStorage.getItem('activeSport') as SportId | null;
    if (saved && SPORTS.some(s => s.id === saved)) {
      activeSport.value = saved;
    }
  });

  const context: SportContext = {
    activeSport,
    sports: SPORTS,
    change: (sportId: SportId) => {
      activeSport.value = sportId;
      localStorage.setItem('activeSport', sportId);
    },
  };

  useContextProvider(SportContextId, context);

  return context;
}
\`\`\`

### Using State in Components

\`\`\`typescript
// src/components/SportSelector.tsx
import { component$ } from '@builder.io/qwik';
import { Button } from '@qwik-ui/styled';
import { useSport } from '~/lib/stores/sport.context';

export const SportSelector = component$(() => {
  const { activeSport, sports, change } = useSport();

  return (
    <nav class="flex gap-2">
      {sports.map((sport) => (
        <Button
          key={sport.id}
          variant={activeSport.value === sport.id ? 'primary' : 'outline'}
          onClick$={() => change(sport.id)}
        >
          {sport.display}
        </Button>
      ))}
    </nav>
  );
});
\`\`\`

---

## Internationalization (i18n)

### Using qwik-speak

\`\`\`typescript
// src/lib/i18n/index.ts
import { \$translate as t, plural as p } from 'qwik-speak';

export { t, p };

export const config = {
  defaultLocale: { lang: 'en' },
  supportedLocales: [
    { lang: 'en' },
    { lang: 'es' },
    { lang: 'de' },
    { lang: 'pt' },
    { lang: 'it' },
  ],
  assets: [
    'home',
    'common',
    'entity',
    'nav',
  ],
};
\`\`\`

### Translation Files

\`\`\`json
// src/lib/i18n/translations/en/home.json
{
  "title": "Sports News & Statistics",
  "selectSport": "Select a sport to get started",
  "searchPlaceholder": "Search for a player or team..."
}
\`\`\`

### Usage in Components

\`\`\`typescript
import { component$ } from '@builder.io/qwik';
import { \$translate as t } from 'qwik-speak';

export const HomePage = component$(() => {
  return (
    <div>
      <h1>{t('home.title')}</h1>
      <p>{t('home.selectSport')}</p>
    </div>
  );
});
\`\`\`

---

## API Integration

### API Client Configuration

\`\`\`typescript
// src/lib/api/client.ts
const API_BASE = import.meta.env.PUBLIC_API_URL || '/api/v1';

export interface ApiError {
  message: string;
  status: number;
  code?: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = \`\${this.baseUrl}\${endpoint}\`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error: ApiError = {
        message: \`API error: \${response.status} \${response.statusText}\`,
        status: response.status,
      };
      
      try {
        const data = await response.json();
        error.message = data.message || error.message;
        error.code = data.code;
      } catch {
        // Response wasn't JSON
      }
      
      throw error;
    }

    return response.json();
  }

  get<T>(endpoint: string): Promise<T> {
    return this.fetch<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.fetch<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiClient();
\`\`\`

### Entity API Functions

\`\`\`typescript
// src/lib/api/entities.ts
import { api } from './client';
import type { EntityResponse, EntityType, SportId } from './types';

export interface GetEntityOptions {
  includeWidget?: boolean;
  includeNews?: boolean;
  includeEnhanced?: boolean;
  includeStats?: boolean;
  refresh?: boolean;
}

export async function getEntity(
  entityType: EntityType,
  entityId: string,
  sport: SportId,
  options: GetEntityOptions = {}
): Promise<EntityResponse> {
  const params = new URLSearchParams({ sport });
  
  const includes: string[] = [];
  if (options.includeWidget !== false) includes.push('widget');
  if (options.includeNews) includes.push('news');
  if (options.includeEnhanced) includes.push('enhanced');
  if (options.includeStats) includes.push('stats');
  
  if (includes.length > 0) {
    params.append('include', includes.join(','));
  }
  
  if (options.refresh) {
    params.append('refresh', 'true');
  }

  return api.get<EntityResponse>(\`/entity/\${entityType}/\${entityId}?\${params}\`);
}
\`\`\`

---

## Component Migration Plan

### Component Mapping (Svelte → Qwik)

| Svelte Component | Qwik Component | Notes |
|-----------------|----------------|-------|
| \`Header.svelte\` | \`Header.tsx\` | Use Qwik UI navigation components |
| \`Footer.svelte\` | \`Footer.tsx\` | Direct port with Tailwind |
| \`SearchForm.svelte\` | \`SearchForm.tsx\` | Use Qwik UI Input + Combobox |
| \`EntityAutocomplete.svelte\` | \`EntityAutocomplete.tsx\` | Use Qwik UI Combobox |
| \`Widget.svelte\` | \`Widget.tsx\` | Use Qwik UI Card |

### Migration Guidelines

1. **One component at a time**: Migrate in order of dependency (low → high)
2. **Type everything**: Add explicit TypeScript interfaces for all props
3. **Use Qwik UI**: Replace custom implementations with Qwik UI where possible
4. **Test after each migration**: Ensure functionality parity

### Example Migration: SearchForm

**Original (Svelte):**
\`\`\`svelte
<script lang="ts">
  import { activeSport } from '\$lib/stores/index';
  export let inline = false;
</script>

<form class="field border" class:inline>
  <input type="text" placeholder="Search..." />
</form>
\`\`\`

**Migrated (Qwik):**
\`\`\`typescript
import { component$, useSignal } from '@builder.io/qwik';
import { Input } from '@qwik-ui/styled';
import { useSport } from '~/lib/stores/sport.context';
import { useNavigate } from '@builder.io/qwik-city';

interface SearchFormProps {
  inline?: boolean;
}

export const SearchForm = component$<SearchFormProps>(({ inline = false }) => {
  const { activeSport } = useSport();
  const searchQuery = useSignal('');
  const navigate = useNavigate();

  return (
    <form
      class={['field', inline && 'inline']}
      preventdefault:submit
      onSubmit$={() => {
        if (searchQuery.value) {
          navigate(\`/search?q=\${searchQuery.value}&sport=\${activeSport.value}\`);
        }
      }}
    >
      <Input
        type="text"
        placeholder="Search for a player or team..."
        value={searchQuery.value}
        onInput$={(_, el) => { searchQuery.value = el.value; }}
      />
    </form>
  );
});
\`\`\`

---

## Testing Strategy

### Unit Testing with Vitest

\`\`\`typescript
// tests/unit/components/SportSelector.test.tsx
import { describe, it, expect } from 'vitest';
import { createDOM } from '@builder.io/qwik/testing';
import { SportSelector } from '~/components/SportSelector';

describe('SportSelector', () => {
  it('renders all sports', async () => {
    const { screen, render } = await createDOM();
    await render(<SportSelector />);
    
    expect(screen.querySelector('button')).toBeTruthy();
    expect(screen.textContent).toContain('NBA');
    expect(screen.textContent).toContain('NFL');
    expect(screen.textContent).toContain('Football');
  });
});
\`\`\`

### E2E Testing with Playwright

\`\`\`typescript
// tests/e2e/home.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load and display sport selector', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.getByRole('heading', { name: /sports news/i })).toBeVisible();
    await expect(page.getByRole('button', { name: 'NBA' })).toBeVisible();
  });

  test('should change sport when clicked', async ({ page }) => {
    await page.goto('/');
    
    await page.getByRole('button', { name: 'NFL' }).click();
    
    // Verify sport changed (e.g., via URL, localStorage, or visual indicator)
    await expect(page.getByRole('button', { name: 'NFL' })).toHaveClass(/primary/);
  });
});
\`\`\`

### Test Coverage Goals

| Area | Target Coverage |
|------|----------------|
| Components | 80% |
| API utilities | 90% |
| State stores | 90% |
| E2E critical paths | 100% |

---

## Build & Deployment

### Build Configuration

\`\`\`typescript
// vite.config.ts
import { defineConfig } from 'vite';
import { qwikVite } from '@builder.io/qwik/optimizer';
import { qwikCity } from '@builder.io/qwik-city/vite';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig(() => {
  return {
    plugins: [
      qwikCity(),
      qwikVite(),
      tsconfigPaths(),
    ],
    preview: {
      headers: {
        'Cache-Control': 'public, max-age=600',
      },
    },
  };
});
\`\`\`

### Vercel Deployment

\`\`\`json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "qwik-city",
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.11"
    }
  },
  "rewrites": [
    { "source": "/api/:path*", "destination": "/api/:path*" },
    { "source": "/(.*)", "destination": "/" }
  ]
}
\`\`\`

### NPM Scripts

\`\`\`json
{
  "scripts": {
    "dev": "vite --mode ssr",
    "build": "qwik build",
    "build.client": "vite build",
    "build.preview": "vite build --ssr src/entry.preview.tsx",
    "build.types": "tsc --noEmit",
    "preview": "qwik build preview && vite preview --open",
    "start": "vite --mode ssr --open",
    "lint": "eslint \"src/**/*.{ts,tsx}\"",
    "lint:fix": "eslint \"src/**/*.{ts,tsx}\" --fix",
    "fmt": "prettier --write \"src/**/*.{ts,tsx}\"",
    "test": "vitest",
    "test:e2e": "playwright test",
    "check": "tsc --noEmit && npm run lint"
  }
}
\`\`\`

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| \`PUBLIC_API_URL\` | Backend API URL (default: \`/api/v1\`) | No |
| \`VERCEL\` | Set automatically by Vercel | No |

---

## Development Phases

### Phase 1: Foundation (Week 1-2)

- [ ] Initialize Qwik project with TypeScript
- [ ] Configure Qwik UI Styled Kit + Tailwind
- [ ] Set up project structure
- [ ] Configure ESLint + Prettier
- [ ] Set up path aliases
- [ ] Create base types (\`src/lib/api/types.ts\`)
- [ ] Implement API client
- [ ] Create theme context with dark mode
- [ ] Create sport context

### Phase 2: Core Components (Week 2-3)

- [ ] Build Header component with navigation
- [ ] Build Footer component
- [ ] Build SearchForm component
- [ ] Build EntityAutocomplete with Qwik UI Combobox
- [ ] Build Widget component with Qwik UI Card
- [ ] Build error boundary component
- [ ] Build loading skeleton components

### Phase 3: Routing & Pages (Week 3-4)

- [ ] Implement root layout with providers
- [ ] Build Home page with sport selector
- [ ] Build Player detail page
- [ ] Build Team detail page
- [ ] Build Entity generic page
- [ ] Build Mentions/News page
- [ ] Implement 404 and error pages

### Phase 4: i18n & Polish (Week 4-5)

- [ ] Set up qwik-speak
- [ ] Migrate all translation files
- [ ] Implement language selector
- [ ] Add loading states throughout
- [ ] Add proper meta tags for SEO
- [ ] Implement accessibility improvements
- [ ] Performance optimization

### Phase 5: Testing & Deployment (Week 5-6)

- [ ] Write unit tests for components
- [ ] Write unit tests for utilities
- [ ] Write E2E tests for critical paths
- [ ] Configure CI/CD pipeline
- [ ] Deploy to Vercel staging
- [ ] Performance testing
- [ ] Final QA and bug fixes
- [ ] Production deployment

---

## Best Practices & Guidelines

### TypeScript Guidelines

1. **No implicit \`any\`**: Always define types explicitly
2. **Use interfaces for objects**: Prefer \`interface\` over \`type\` for object shapes
3. **Const assertions**: Use \`as const\` for literal types
4. **Generic constraints**: Use \`extends\` to constrain generics
5. **Discriminated unions**: Use for complex state
6. **Readonly when possible**: Use \`readonly\` and \`Readonly<T>\`

\`\`\`typescript
// ✅ Good
interface Props {
  readonly title: string;
  items: readonly string[];
  onSelect: (item: string) => void;
}

// ❌ Bad
type Props = {
  title: any;
  items: string[];
  onSelect: Function;
};
\`\`\`

### Component Guidelines

1. **Single responsibility**: One component, one job
2. **Props interface**: Always define and export
3. **Default exports**: Use for route components only
4. **Named exports**: Use for regular components
5. **Colocation**: Keep styles and tests near components

\`\`\`typescript
// ✅ Good
export interface ButtonProps {
  variant?: 'primary' | 'secondary';
  children: JSXChildren;
  onClick$?: () => void;
}

export const Button = component$<ButtonProps>((props) => {
  // ...
});
\`\`\`

### State Management Guidelines

1. **Use signals**: For local reactive state
2. **Use context**: For shared state across components
3. **Use routeLoader$**: For server-side data fetching
4. **Avoid prop drilling**: Use context for deep trees
5. **Keep state minimal**: Only store what's necessary

### Performance Guidelines

1. **Lazy load**: Use \`component$\` (automatic lazy loading)
2. **Avoid inline functions in JSX**: Use \`onClick$\` handlers
3. **Use \`useVisibleTask$\` sparingly**: Prefer SSR
4. **Optimize images**: Use proper formats and sizing
5. **Bundle analysis**: Regularly check bundle size

---

## References

- [Qwik Documentation](https://qwik.builder.io/docs/)
- [Qwik City Documentation](https://qwik.builder.io/docs/qwikcity/)
- [Qwik UI Documentation](https://qwikui.com/docs/styled/introduction/)
- [qwik-speak Documentation](https://github.com/robisim74/qwik-speak)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Scoracle Backend API Docs](/api/docs)

---

## Appendix: Migration Checklist

### Pre-Migration

- [ ] Audit current SvelteKit features in use
- [ ] Document all API endpoints used
- [ ] Export all translation files
- [ ] Document current routing structure
- [ ] Identify third-party dependencies

### During Migration

- [ ] Component by component migration
- [ ] Test each migrated component
- [ ] Maintain feature parity
- [ ] Regular check-ins with stakeholders

### Post-Migration

- [ ] Full regression testing
- [ ] Performance comparison
- [ ] Documentation update
- [ ] Team training on Qwik
- [ ] Deprecate SvelteKit codebase

---

*Last updated: December 2024*
