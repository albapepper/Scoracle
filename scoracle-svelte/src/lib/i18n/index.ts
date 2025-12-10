/**
 * i18n setup - initializes svelte-i18n
 * Import this file in your root layout to enable translations
 */
import { browser } from '$app/environment';
import { init, register, getLocaleFromNavigator } from 'svelte-i18n';

// Register translation files (lazy loaded)
register('en', () => import('./translations/en.json'));
register('es', () => import('./translations/es.json'));
register('de', () => import('./translations/de.json'));
register('pt', () => import('./translations/pt.json'));
register('it', () => import('./translations/it.json'));

function getInitialLocale(): string {
  if (!browser) return 'en';
  
  // Check localStorage first
  try {
    const saved = localStorage.getItem('language');
    if (saved && ['en', 'es', 'de', 'pt', 'it'].includes(saved)) {
      return saved;
    }
  } catch {
    // localStorage not available
  }

  // Fall back to browser locale
  const browserLocale = getLocaleFromNavigator();
  if (browserLocale) {
    const lang = browserLocale.split('-')[0];
    if (['en', 'es', 'de', 'pt', 'it'].includes(lang)) {
      return lang;
    }
  }

  return 'en';
}

// Initialize i18n
init({
  fallbackLocale: 'en',
  initialLocale: getInitialLocale(),
});

