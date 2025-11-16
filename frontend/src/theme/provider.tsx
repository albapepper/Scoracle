import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { MantineProvider, createTheme } from '@mantine/core';
import theme, { ColorScheme } from './tokens';

interface ThemeModeValue {
  colorScheme: ColorScheme;
  setColorScheme: (scheme: ColorScheme) => void;
  toggleColorScheme: () => void;
}

const createLightMantineTheme = () => {
  const lightColors = theme.light.colors;
  return createTheme({
    colors: {
      // Anthropic-inspired color scale
      primary: ['#F7FAFC','#EDF2F7','#E2E8F0','#CBD5E0','#A0AEC0','#718096','#4A5568','#2D3748','#1A202C','#171923'],
      accent: ['#EBF8FF','#BEE3F8','#90CDF4','#63B3ED','#4299E1','#3182CE','#2C5282','#2A4365','#1A365D','#153450']
    },
    primaryColor: 'primary',
    fontFamily: theme.typography.fontFamily.primary,
    headings: { fontFamily: theme.typography.fontFamily.primary },
    components: {
      Button: { defaultProps: { color: 'primary' } },
      Card: { styles: { root: { backgroundColor: lightColors.background.tertiary, borderColor: 'transparent', borderWidth: '0px' } } },
      Paper: { styles: { root: { backgroundColor: lightColors.background.tertiary, borderColor: 'transparent', borderWidth: '0px' } } },
    },
  // Mantine v5 no longer accepts top-level colorScheme; we control via our context.
    other: { colors: lightColors, typography: theme.typography, spacing: theme.spacing, borderRadius: theme.borderRadius, boxShadow: theme.boxShadow.light },
  });
};

const createDarkMantineTheme = () => {
  const darkColors = theme.dark.colors;
  return createTheme({
    colors: {
      // Burnt ember orange color scale for buttons (Claude.ai style)
      primary: ['#6B3F2A','#7D4A33','#8F563D','#A15E46','#A85A39','#B8674A','#C97A56','#D98C64','#E99D73','#F9AE82'],
      accent: ['#153450','#1A365D','#2A4365','#2C5282','#3182CE','#4299E1','#63B3ED','#90CDF4','#BEE3F8','#EBF8FF']
    },
    primaryColor: 'primary',
    fontFamily: theme.typography.fontFamily.primary,
    headings: { fontFamily: theme.typography.fontFamily.primary },
    components: {
      Button: { defaultProps: { color: 'primary' } },
      Card: { styles: { root: { backgroundColor: darkColors.background.secondary, borderColor: darkColors.ui.border, color: darkColors.text.primary, borderWidth: '1px' } } },
      Paper: { styles: { root: { backgroundColor: darkColors.background.secondary, borderColor: darkColors.ui.border, color: darkColors.text.primary, borderWidth: '1px' } } },
    },
  // Mantine v5 no longer accepts top-level colorScheme; we control via our context.
    other: { colors: darkColors, typography: theme.typography, spacing: theme.spacing, borderRadius: theme.borderRadius, boxShadow: theme.boxShadow.dark },
  });
};

const ThemeModeContext = createContext<ThemeModeValue | null>(null);
export const useThemeMode = () => {
  const ctx = useContext(ThemeModeContext);
  if (!ctx) throw new Error('useThemeMode must be used within ThemeProvider');
  return ctx;
};

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const getInitial = (): ColorScheme => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('color-scheme') : null;
    if (saved === 'dark' || saved === 'light') return saved;
    if (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  };
  const [colorScheme, setColorScheme] = useState<ColorScheme>(getInitial);
  useEffect(() => { try { localStorage.setItem('color-scheme', colorScheme); } catch (_) {} }, [colorScheme]);
  const mantineTheme = useMemo(() => (colorScheme === 'dark' ? createDarkMantineTheme() : createLightMantineTheme()), [colorScheme]);
  const value = useMemo<ThemeModeValue>(() => ({ colorScheme, setColorScheme, toggleColorScheme: () => setColorScheme((p) => (p === 'dark' ? 'light' : 'dark')) }), [colorScheme]);
  return (
    <ThemeModeContext.Provider value={value}>
      <MantineProvider theme={mantineTheme}>
        {children}
      </MantineProvider>
    </ThemeModeContext.Provider>
  );
};

export default ThemeProvider;
