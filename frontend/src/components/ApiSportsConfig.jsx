import React, { useMemo } from 'react';
import { APISPORTS_KEY } from '../config';
import { useLanguage } from '../context/LanguageContext';
import { useSportContext } from '../context/SportContext';
import { useThemeMode } from '../ThemeProvider';

const SPORT_HOSTS = {
  football: 'https://v3.football.api-sports.io/',
  soccer: 'https://v3.football.api-sports.io/',
  baseball: 'https://v1.baseball.api-sports.io/',
  basketball: 'https://v1.basketball.api-sports.io/',
  nba: 'https://v2.nba.api-sports.io/',
  hockey: 'https://v1.hockey.api-sports.io/',
  rugby: 'https://v1.rugby.api-sports.io/',
  volleyball: 'https://v1.volleyball.api-sports.io/',
  handball: 'https://v1.handball.api-sports.io/',
  nfl: 'https://v1.american-football.api-sports.io/',
  afl: 'https://v1.afl.api-sports.io/',
  mma: 'https://v1.mma.api-sports.io/',
  f1: 'https://v1.formula-1.api-sports.io/',
};

// Renders a single global config widget. Place once near the app root.
export default function ApiSportsConfig({
  apiKey,
  sport,
  lang,
  theme = 'auto',
  showError = true,
  showLogos = true,
  refresh = 20,
  targets,
  style,
}) {
  const { language } = useLanguage();
  const { activeSport } = useSportContext();
  const { colorScheme } = useThemeMode();
  // Resolve sport preference: explicit prop wins over context
  const resolvedSportRaw = (sport || activeSport || 'FOOTBALL').toString();

  const final = useMemo(() => {
    const sportLower = resolvedSportRaw.toLowerCase();

    const config = {
      key: apiKey || APISPORTS_KEY,
      sport: sportLower,
      lang: (lang || language || 'en').toLowerCase(),
      // Map app color scheme to widget theme: light -> white, dark -> grey
      theme: theme === 'auto' ? (colorScheme === 'dark' ? 'grey' : 'white') : theme,
      'show-error': String(showError),
      'show-logos': String(showLogos),
    };

    if (refresh !== undefined && refresh !== null) {
      config.refresh = String(refresh);
    }

    if (targets && typeof targets === 'object') {
      Object.entries(targets).forEach(([key, selector]) => {
        if (!selector) return;
        const kebab = key
          .replace(/([a-z])([A-Z])/g, '$1-$2')
          .replace(/_/g, '-')
          .toLowerCase();
        config[`target-${kebab}`] = selector;
      });
    }

    const host = SPORT_HOSTS[sportLower];
    if (host) {
      config[`url-${sportLower}`] = host;
      config.host = host;
    }

    return config;
  }, [
    apiKey,
    lang,
    theme,
    showError,
    showLogos,
    refresh,
    targets,
    language,
    colorScheme,
    resolvedSportRaw,
  ]);

  return (
    <api-sports-widget
      data-type="config"
      {...Object.fromEntries(Object.entries(final).map(([key, value]) => [`data-${key}`, String(value)]))}
    />
  );
}
