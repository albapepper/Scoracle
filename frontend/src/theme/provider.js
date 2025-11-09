import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { MantineProvider, createTheme } from '@mantine/core';
import theme from './tokens';

const createLightMantineTheme = () => {
  const lightColors = theme.light.colors;
  return createTheme({
    colors: {
      primary: ['#f0f4f8','#e2e8f0','#cbd5e0','#a0b0c0','#8096af','#66809f','#546a7b','#455b70','#364c63','#273b52'],
      accent: ['#edf2eb','#dae5d6','#c7d8c1','#b4cbad','#a1be99','#8eb185','#879e7e','#748a6c','#607658','#4d6247']
    },
    primaryColor: 'primary',
    components: {
      Button: { defaultProps: { color: 'primary' } },
      Card: { styles: { root: { backgroundColor: lightColors.background.secondary, borderColor: lightColors.ui.border } } },
      Paper: { styles: { root: { backgroundColor: lightColors.background.secondary, borderColor: lightColors.ui.border } } },
    },
    colorScheme: 'light',
    other: { colors: lightColors, typography: theme.typography, spacing: theme.spacing, borderRadius: theme.borderRadius, boxShadow: theme.boxShadow.light },
    globalStyles: () => ({
      body: { backgroundColor: lightColors.background.primary, color: lightColors.text.primary, fontFamily: "'Source Sans Pro', 'Segoe UI', sans-serif" },
      a: { color: lightColors.ui.primary, '&:hover': { color: lightColors.ui.secondary } },
      h1: { fontFamily: "'Source Serif Pro', Georgia, serif" },
      h2: { fontFamily: "'Source Serif Pro', Georgia, serif" },
      h3: { fontFamily: "'Source Serif Pro', Georgia, serif" },
      h4: { fontFamily: "'Source Serif Pro', Georgia, serif" },
      h5: { fontFamily: "'Source Serif Pro', Georgia, serif" },
      h6: { fontFamily: "'Source Serif Pro', Georgia, serif" },
    }),
  });
};

const createDarkMantineTheme = () => {
  const darkColors = theme.dark.colors;
  return createTheme({
    colors: {
      primary: ['#e2ecf5','#c5d8eb','#a8c4e1','#8ab0d8','#6d9cce','#5888c5','#3d70b6','#2e56a3','#1f3c90','#10227d'],
      accent: ['#e8f1e0','#d1e3c1','#bad5a2','#a3c783','#8cb964','#75ab45','#5e9d26','#478f07','#308100','#197300']
    },
    primaryColor: 'primary',
    components: {
      Button: { defaultProps: { color: 'primary' } },
      Card: { styles: { root: { backgroundColor: darkColors.background.secondary, borderColor: darkColors.ui.border, color: darkColors.text.primary } } },
      Paper: { styles: { root: { backgroundColor: darkColors.background.secondary, borderColor: darkColors.ui.border, color: darkColors.text.primary } } },
    },
    colorScheme: 'dark',
    other: { colors: darkColors, typography: theme.typography, spacing: theme.spacing, borderRadius: theme.borderRadius, boxShadow: theme.boxShadow.dark },
    globalStyles: () => ({
      body: { backgroundColor: darkColors.background.primary, color: darkColors.text.primary, fontFamily: "'Source Sans Pro', 'Segoe UI', sans-serif" },
      a: { color: darkColors.ui.primary, '&:hover': { color: darkColors.ui.secondary } },
      h1: { fontFamily: "'Source Serif Pro', Georgia, serif" },
      h2: { fontFamily: "'Source Serif Pro', Georgia, serif" },
      h3: { fontFamily: "'Source Serif Pro', Georgia, serif" },
      h4: { fontFamily: "'Source Serif Pro', Georgia, serif" },
      h5: { fontFamily: "'Source Serif Pro', Georgia, serif" },
      h6: { fontFamily: "'Source Serif Pro', Georgia, serif" },
    }),
  });
};

const ThemeModeContext = createContext();
export const useThemeMode = () => useContext(ThemeModeContext);

export const ThemeProvider = ({ children }) => {
  const getInitial = () => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('color-scheme') : null;
    if (saved === 'dark' || saved === 'light') return saved;
    if (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  };
  const [colorScheme, setColorScheme] = useState(getInitial);
  useEffect(() => { try { localStorage.setItem('color-scheme', colorScheme); } catch (_) {} }, [colorScheme]);
  const mantineTheme = useMemo(() => (colorScheme === 'dark' ? createDarkMantineTheme() : createLightMantineTheme()), [colorScheme]);
  const value = useMemo(() => ({ colorScheme, setColorScheme, toggleColorScheme: () => setColorScheme((p) => (p === 'dark' ? 'light' : 'dark')) }), [colorScheme]);
  return (
    <ThemeModeContext.Provider value={value}>
      <MantineProvider theme={mantineTheme} withGlobalStyles withNormalizeCSS>
        {children}
      </MantineProvider>
    </ThemeModeContext.Provider>
  );
};
