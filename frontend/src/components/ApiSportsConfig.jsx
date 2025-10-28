import React, { useMemo } from 'react';
import ApiSportsWidget from './ApiSportsWidget';
import { APISPORTS_KEY } from '../config';
import { useLanguage } from '../context/LanguageContext';
import { useSportContext } from '../context/SportContext';
import { useThemeMode } from '../ThemeProvider';

// Renders a single global config widget. Place once near the app root.
export default function ApiSportsConfig({
  apiKey,
  sport,
  lang,
  theme = 'auto',
  showErrors = true,
  showLogos = true,
  style,
}) {
  const { language } = useLanguage();
  const { activeSport } = useSportContext();
  const { colorScheme } = useThemeMode();

  const final = useMemo(() => ({
    key: apiKey || APISPORTS_KEY,
    sport: (sport || activeSport || 'FOOTBALL').toString().toLowerCase(),
    lang: (lang || language || 'en').toLowerCase(),
    // Map app color scheme to widget theme: light -> white, dark -> grey
    theme: theme === 'auto' ? (colorScheme === 'dark' ? 'grey' : 'white') : theme,
    'show-errors': String(showErrors),
    'show-logos': String(showLogos),
  }), [apiKey, sport, lang, theme, showErrors, showLogos, language, activeSport, colorScheme]);

  return (
    <ApiSportsWidget
      type="config"
      sport={activeSport}
      data={final}
      style={style}
    />
  );
}
