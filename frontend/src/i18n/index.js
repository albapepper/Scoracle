import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      header: {
        settings: 'Settings',
        appearance: 'Appearance',
        darkMode: 'Dark mode',
        language: 'Language',
        menu: 'Menu',
      },
      common: {
        home: 'Home',
        returnHome: 'Return to Home',
        loading: 'Loading...',
        failedLoad: 'Failed to load. Please try again later.',
      },
    },
  },
  es: {
    translation: {
      header: {
        settings: 'Ajustes',
        appearance: 'Apariencia',
        darkMode: 'Modo oscuro',
        language: 'Idioma',
        menu: 'Menú',
      },
      common: {
        home: 'Inicio',
        returnHome: 'Volver al inicio',
        loading: 'Cargando...',
        failedLoad: 'Error al cargar. Inténtalo de nuevo más tarde.',
      },
    },
  },
  de: {
    translation: {
      header: {
        settings: 'Einstellungen',
        appearance: 'Erscheinungsbild',
        darkMode: 'Dunkelmodus',
        language: 'Sprache',
        menu: 'Menü',
      },
      common: {
        home: 'Startseite',
        returnHome: 'Zur Startseite',
        loading: 'Wird geladen...',
        failedLoad: 'Laden fehlgeschlagen. Bitte später erneut versuchen.',
      },
    },
  },
  fr: {
    translation: {
      header: {
        settings: 'Paramètres',
        appearance: 'Apparence',
        darkMode: 'Mode sombre',
        language: 'Langue',
        menu: 'Menu',
      },
      common: {
        home: 'Accueil',
        returnHome: 'Retour à l\'accueil',
        loading: 'Chargement...',
        failedLoad: 'Échec du chargement. Veuillez réessayer plus tard.',
      },
    },
  },
  it: {
    translation: {
      header: {
        settings: 'Impostazioni',
        appearance: 'Aspetto',
        darkMode: 'Modalità scura',
        language: 'Lingua',
        menu: 'Menu',
      },
      common: {
        home: 'Home',
        returnHome: 'Torna alla Home',
        loading: 'Caricamento...',
        failedLoad: 'Caricamento non riuscito. Riprova più tardi.',
      },
    },
  },
};

// Initialize i18n
i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
  });

export default i18n;
