// Theme tokens and helpers (TypeScript)

export type ColorScheme = 'light' | 'dark';

export interface ThemeColors {
  background: { primary: string; secondary: string; tertiary: string };
  text: { primary: string; secondary: string; accent: string; muted: string };
  ui: { primary: string; secondary: string; accent: string; border: string };
  visualization: { primary: string; secondary: string; tertiary: string; quaternary: string; quintary: string; percentiles: string[] };
  status: { success: string; warning: string; error: string; info: string };
}

export interface ThemeTokens {
  light: { colors: ThemeColors };
  dark: { colors: ThemeColors };
  typography: {
    fontFamily: { primary: string; secondary: string };
    fontWeight: { light: number; regular: number; medium: number; semibold: number; bold: number };
    lineHeight: { tight: number; base: number; relaxed: number };
  };
  spacing: Record<'xs'|'sm'|'md'|'lg'|'xl'|'xxl', string>;
  borderRadius: Record<'sm'|'md'|'lg'|'xl'|'full', string>;
  boxShadow: { light: Record<'sm'|'md'|'lg'|'xl', string>; dark: Record<'sm'|'md'|'lg'|'xl', string> };
  header?: Record<ColorScheme, { gradientStart: string; gradientEnd: string; title: { color: string; strokeWidth: string; strokeColor: string; textShadow: string } }>;
}

const theme: ThemeTokens = {
  light: {
    colors: {
      background: { primary: '#f8f8f5', secondary: '#f3efe6', tertiary: '#e8e8e2' },
      text: { primary: '#333333', secondary: '#666666', accent: '#3d4c53', muted: '#929292' },
      ui: { primary: '#546a7b', secondary: '#728ca0', accent: '#879e7e', border: '#d9d9d6' },
      visualization: {
        primary: '#546a7b', secondary: '#879e7e', tertiary: '#a87d5f', quaternary: '#8b6d8a', quintary: '#6a7a77',
        percentiles: ['#d8e2ec','#b0c4d4','#879eb8','#61799d','#3d5680']
      },
      status: { success: '#879e7e', warning: '#c9b178', error: '#b37264', info: '#728ca0' }
    },
  },
  dark: {
    colors: {
      background: { primary: '#222220', secondary: '#2a2a27', tertiary: '#323230' },
      text: { primary: '#e8e8e8', secondary: '#b8b8b8', accent: '#d4dce1', muted: '#7a7a7a' },
      ui: { primary: '#8ab4d1', secondary: '#6d96b8', accent: '#a8c98a', border: '#3a3a36' },
      visualization: {
        primary: '#8ab4d1', secondary: '#a8c98a', tertiary: '#d4a876', quaternary: '#c9afc9', quintary: '#95a9a5',
        percentiles: ['#3a4452','#4a5f73','#5a7a94','#7a9bb5','#8ab4d1']
      },
      status: { success: '#a8c98a', warning: '#d4b876', error: '#d4876a', info: '#8ab4d1' }
    },
  },
  typography: {
    fontFamily: { primary: "'Source Serif Pro', Georgia, serif", secondary: "'Source Sans Pro', 'Segoe UI', sans-serif" },
    fontWeight: { light: 300, regular: 400, medium: 500, semibold: 600, bold: 700 },
    lineHeight: { tight: 1.2, base: 1.5, relaxed: 1.8 },
  },
  spacing: { xs: '0.25rem', sm: '0.5rem', md: '1rem', lg: '1.5rem', xl: '2rem', xxl: '3rem' },
  borderRadius: { sm: '2px', md: '4px', lg: '8px', xl: '16px', full: '9999px' },
  boxShadow: {
    light: { sm: '0 1px 2px rgba(0, 0, 0, 0.05)', md: '0 2px 4px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.07)', lg: '0 4px 6px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.06)', xl: '0 10px 15px rgba(0, 0, 0, 0.03), 0 4px 6px rgba(0, 0, 0, 0.05)' },
    dark: { sm: '0 1px 3px rgba(0, 0, 0, 0.3)', md: '0 2px 6px rgba(0, 0, 0, 0.3), 0 1px 3px rgba(0, 0, 0, 0.2)', lg: '0 4px 12px rgba(0, 0, 0, 0.4), 0 2px 4px rgba(0, 0, 0, 0.2)', xl: '0 10px 20px rgba(0, 0, 0, 0.4), 0 4px 8px rgba(0, 0, 0, 0.2)' },
  },
};

theme.header = {
  light: {
    gradientStart: '#2b6fb4', gradientEnd: '#1e5aa0',
    title: { color: '#ffffff', strokeWidth: '1.25px', strokeColor: 'rgba(0,0,0,0.9)', textShadow: '0 0 1px rgba(0,0,0,0.6), 0 1px 0 rgba(0,0,0,0.6)' }
  },
  dark: {
    gradientStart: '#2d3f4f', gradientEnd: '#1f2d39',
    title: { color: '#e8e8e8', strokeWidth: '0.5px', strokeColor: 'rgba(0,0,0,0.3)', textShadow: '0 1px 2px rgba(0,0,0,0.5)' }
  }
};

export const getThemeColors = (colorScheme: ColorScheme = 'light'): ThemeColors => theme[colorScheme]?.colors || theme.light.colors;
export const getBoxShadow = (colorScheme: ColorScheme = 'light') => theme.boxShadow[colorScheme] || theme.boxShadow.light;

export default theme;
