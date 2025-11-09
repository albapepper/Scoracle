import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
	en: {
		translation: {
			search_placeholder: 'Search entities...',
			mentions_heading: 'Mentions',
			entity_heading: 'Entity',
			not_found_message: 'Page not found',
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
