import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

export interface MentionsNS {
  rankingsTab: string;
  linkedTeams: string;
  linkedPlayers: string;
}

interface BaseTranslation {
  search_placeholder: string;
  mentions_heading: string;
  entity_heading: string;
  not_found_message: string;
  language_changed: string; // interpolation {{lng}}
  mentions: MentionsNS;
}

export interface ResourcesShape {
  en: { translation: BaseTranslation };
  es: { translation: BaseTranslation };
}

const resources: ResourcesShape & Record<string, any> = {
  en: {
    translation: {
      search_placeholder: 'Search entities...',
      mentions_heading: 'Mentions',
      entity_heading: 'Entity',
      not_found_message: 'Page not found',
      language_changed: 'Language changed to {{lng}}',
      mentions: {
        rankingsTab: 'Rankings',
        linkedTeams: 'Linked teams',
        linkedPlayers: 'Linked players',
      },
    },
  },
  es: {
    translation: {
      search_placeholder: 'Buscar entidades...',
      mentions_heading: 'Menciones',
      entity_heading: 'Entidad',
      not_found_message: 'Página no encontrada',
      language_changed: 'Idioma cambiado a {{lng}}',
      mentions: {
        rankingsTab: 'Rankings',
        linkedTeams: 'Equipos relacionados',
        linkedPlayers: 'Jugadores relacionados',
      },
    },
  },
};

void i18n
  .use(initReactI18next)
  .init({
    resources: resources as any,
    lng: 'en',
    fallbackLng: 'en',
    fallbackNS: 'translation',
    defaultNS: 'translation',
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
  });

export default i18n;