/**
 * Theme store - replaces React ThemeProvider
 */
import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

export type ColorScheme = 'light' | 'dark';

function getInitialTheme(): ColorScheme {
  if (!browser) return 'light';

  try {
    const saved = localStorage.getItem('color-scheme');
    if (saved === 'dark' || saved === 'light') return saved;
  } catch {
    // localStorage not available
  }

  if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }

  return 'light';
}

function applyTheme(scheme: ColorScheme) {
  if (!browser) return;

  const html = document.documentElement;
  html.classList.remove('scoracle-light', 'scoracle-dark', 'dark');

  if (scheme === 'dark') {
    html.classList.add('scoracle-dark', 'dark');
  } else {
    html.classList.add('scoracle-light');
  }

  try {
    localStorage.setItem('color-scheme', scheme);
  } catch {
    // localStorage not available
  }
}

function createThemeStore() {
  const { subscribe, set, update } = writable<ColorScheme>(getInitialTheme());

  // Apply initial theme on creation
  if (browser) {
    applyTheme(getInitialTheme());
  }

  return {
    subscribe,
    set: (scheme: ColorScheme) => {
      applyTheme(scheme);
      set(scheme);
    },
    toggle: () => {
      update((current) => {
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        return next;
      });
    },
  };
}

export const colorScheme = createThemeStore();

// Derived store for checking if dark mode
export const isDark = derived(colorScheme, ($scheme) => $scheme === 'dark');

/**
 * Get theme colors based on current scheme
 */
export function getThemeColors(scheme: ColorScheme) {
  if (scheme === 'dark') {
    return {
      background: {
        primary: '#1A1A1A',
        secondary: '#242424',
        tertiary: '#2D2D2D',
      },
      text: {
        primary: '#F5F5E8',
        secondary: '#D0D0C0',
        accent: '#E8C4A0',
      },
      ui: {
        primary: '#A85A39',
        border: '#404040',
      },
    };
  }

  return {
    background: {
      primary: '#F5F5E8',
      secondary: '#EAEADA',
      tertiary: '#E0E0D0',
    },
    text: {
      primary: '#2D3748',
      secondary: '#4A5568',
      accent: '#1A365D',
    },
    ui: {
      primary: '#2D3748',
      border: '#CBD5E0',
    },
  };
}

