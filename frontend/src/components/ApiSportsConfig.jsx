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
  // Resolve sport preference: explicit prop wins over context
  const resolvedSportRaw = (sport || activeSport || 'FOOTBALL').toString();

  const final = useMemo(() => {
    const sportLower = resolvedSportRaw.toLowerCase();
    // Required host per sport for API-Sports widgets v3
    // Ref: vendor examples (v3.*) expect a data-host like v3.football.api-sports.io
    const hostBySport = {
      football: 'v3.football.api-sports.io',
      epl: 'v3.football.api-sports.io',
      basketball: 'v3.basketball.api-sports.io',
      nba: 'v3.basketball.api-sports.io',
      'american-football': 'v3.american-football.api-sports.io',
      nfl: 'v3.american-football.api-sports.io',
    };
    const host = hostBySport[sportLower] || 'v3.football.api-sports.io';

    return {
      key: apiKey || APISPORTS_KEY,
      host,
      sport: sportLower,
      lang: (lang || language || 'en').toLowerCase(),
      // Map app color scheme to widget theme: light -> white, dark -> grey
      theme: theme === 'auto' ? (colorScheme === 'dark' ? 'grey' : 'white') : theme,
      'show-errors': String(showErrors),
    };
  }, [apiKey, lang, theme, showErrors, language, colorScheme, resolvedSportRaw]);

  return (
    <ApiSportsWidget
      type="config"
      sport={resolvedSportRaw}
      data={final}
      style={style}
    />
  );
}
