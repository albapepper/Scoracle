import React from 'react';
import { MantineProvider, createTheme } from '@mantine/core';
import theme from './theme';

// Convert our theme to Mantine's format
const mantineTheme = createTheme({
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
  },
  
  // Set color scheme
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
  globalStyles: (theme) => ({
    body: {
      backgroundColor: '#f8f8f5', // Eggshell background
      color: '#333333', // Dark text
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

/**
 * ThemeProvider component that wraps the application
 * with our custom theme settings
 */
export const ThemeProvider = ({ children }) => {
  return (
    <MantineProvider theme={mantineTheme} withGlobalStyles withNormalizeCSS>
      {children}
    </MantineProvider>
  );
};

export { theme as rawTheme };
export default theme;