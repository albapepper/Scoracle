/**
 * Theme store - replaces React ThemeProvider
 * Updated for BeerCSS dark mode support
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
  
  // BeerCSS uses 'dark' class on html element
  if (scheme === 'dark') {
    html.classList.add('dark');
    html.classList.remove('light');
  } else {
    html.classList.add('light');
    html.classList.remove('dark');
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

