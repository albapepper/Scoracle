import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
	en: {
		translation: {
			search_placeholder: 'Search entities...',
			mentions_heading: 'Mentions',
			entity_heading: 'Entity',
			not_found_message: 'Page not found',
			language_changed: 'Language changed to {{lng}}',
			// Mentions UI
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
			// UI de Menciones
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
		resources,
		lng: 'en',
		fallbackLng: 'en',
		interpolation: { escapeValue: false },
		react: { useSuspense: false },
	});

export default i18n;
