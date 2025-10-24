import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { MantineProvider, createTheme } from '@mantine/core';
import theme from './theme';

// Convert our theme to Mantine's format
const baseMantineTheme = createTheme({
  colors: {
    // Create a custom color palette based on our theme
    primary: [
      '#f0f4f8', // 0 - lightest
      '#e2e8f0',
      '#cbd5e0',
      '#a0b0c0',
      '#8096af',
      '#66809f',
      '#546a7b', // 6 - our primary color
      '#455b70',
      '#364c63',
      '#273b52', // 9 - darkest
    ],
    accent: [
      '#edf2eb',
      '#dae5d6',
      '#c7d8c1',
      '#b4cbad',
      '#a1be99',
      '#8eb185',
      '#879e7e', // Our accent color
      '#748a6c',
      '#607658',
      '#4d6247',
    ]
  },
  
  primaryColor: 'primary', // Set the primary color
  
  // Set global styles
  components: {
    Button: {
      defaultProps: {
        color: 'primary',
      },
    },
    Card: {
      styles: {
        root: {
          backgroundColor: theme.colors.background.secondary,
        },
      },
    },
    Paper: {
      styles: {
        root: {
          backgroundColor: theme.colors.background.secondary,
        },
      },
    },
  },
  
  // default; will be overridden by provider state
  colorScheme: 'light',
  
  // Override default Mantine theme values
  other: {
    colors: theme.colors,
    typography: theme.typography,
    spacing: theme.spacing,
    borderRadius: theme.borderRadius,
    boxShadow: theme.boxShadow,
  },
  
  // Custom global styles
  globalStyles: (mantineTheme) => ({
    body: {
      backgroundColor: theme.colors.background.primary, // Eggshell background from our tokens
      color: theme.colors.text.primary, // Dark text from tokens
      fontFamily: "'Source Sans Pro', 'Segoe UI', sans-serif",
    },
    a: {
      color: '#546a7b', // Muted blue-slate
      '&:hover': {
        color: '#455b70',
      },
    },
    h1: { fontFamily: "'Source Serif Pro', Georgia, serif" },
    h2: { fontFamily: "'Source Serif Pro', Georgia, serif" },
    h3: { fontFamily: "'Source Serif Pro', Georgia, serif" },
    h4: { fontFamily: "'Source Serif Pro', Georgia, serif" },
    h5: { fontFamily: "'Source Serif Pro', Georgia, serif" },
    h6: { fontFamily: "'Source Serif Pro', Georgia, serif" },
  }),
});

// Color scheme context
const ThemeModeContext = createContext();
export const useThemeMode = () => useContext(ThemeModeContext);

/**
 * ThemeProvider component that wraps the application
 * with our custom theme settings
 */
export const ThemeProvider = ({ children }) => {
  // initialize from localStorage or prefers-color-scheme
  const getInitial = () => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem('color-scheme') : null;
    if (saved === 'dark' || saved === 'light') return saved;
    if (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  };

  const [colorScheme, setColorScheme] = useState(getInitial);

  useEffect(() => {
    try { localStorage.setItem('color-scheme', colorScheme); } catch (_) {}
  }, [colorScheme]);

  const mantineTheme = useMemo(() => ({ ...baseMantineTheme, colorScheme }), [colorScheme]);

  const value = useMemo(() => ({
    colorScheme,
    setColorScheme,
    toggleColorScheme: () => setColorScheme((prev) => (prev === 'dark' ? 'light' : 'dark')),
  }), [colorScheme]);

  return (
    <ThemeModeContext.Provider value={value}>
      <MantineProvider theme={mantineTheme} withGlobalStyles withNormalizeCSS>
        {children}
      </MantineProvider>
    </ThemeModeContext.Provider>
  );
};

export { theme as rawTheme };
export default theme;