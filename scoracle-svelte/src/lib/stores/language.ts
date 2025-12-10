/**
 * Language store - replaces React LanguageContext
 */
import { derived } from 'svelte/store';
import { locale, init, register, getLocaleFromNavigator } from 'svelte-i18n';
import { browser } from '$app/environment';

export interface LanguageInfo {
  id: string;
  display: string;
  label: string;
}

export const languages: LanguageInfo[] = [
  { id: 'en', display: 'English', label: 'EN' },
  { id: 'es', display: 'Español', label: 'ES' },
  { id: 'de', display: 'Deutsch', label: 'DE' },
  { id: 'pt', display: 'Português', label: 'PT' },
  { id: 'it', display: 'Italiano', label: 'IT' },
];

// Register all translation files
register('en', () => import('$lib/i18n/translations/en.json'));
register('es', () => import('$lib/i18n/translations/es.json'));
register('de', () => import('$lib/i18n/translations/de.json'));
register('pt', () => import('$lib/i18n/translations/pt.json'));
register('it', () => import('$lib/i18n/translations/it.json'));

// Initialize i18n - only runs on client
if (browser) {
  init({
    fallbackLocale: 'en',
    initialLocale: getLocaleFromNavigator()?.split('-')[0] || 'en',
  });
} else {
  init({
    fallbackLocale: 'en',
    initialLocale: 'en',
  });
}

/**
 * Change the current language
 */
export function changeLanguage(langId: string) {
  if (languages.some((l) => l.id === langId)) {
    locale.set(langId);
    if (browser) {
      try {
        localStorage.setItem('language', langId);
      } catch {
        // localStorage not available
      }
    }
  }
}

/**
 * Get current language info
 */
export const currentLanguage = derived(locale, ($locale) => {
  const found = languages.find((l) => l.id === $locale);
  return found || languages[0];
});

// Re-export locale for direct subscription
export { locale };

