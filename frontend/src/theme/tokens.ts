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
      // Beige page background with ivory card backgrounds
      background: { primary: '#E8E3D3', secondary: '#F0ECE0', tertiary: '#F5F5E8' },
      // High contrast text for readability
      text: { primary: '#1A1A1A', secondary: '#666666', accent: '#2D3748', muted: '#A0AEC0' },
      // Subtle, professional UI colors
      ui: { primary: '#4A5568', secondary: '#5B7FA8', accent: '#4299E1', border: '#E2E8F0' },
      // Data visualization palette: accessible, distinct colors
      visualization: {
        primary: '#4299E1', secondary: '#48BB78', tertiary: '#ED8936', quaternary: '#9F7AEA', quintary: '#38B2AC',
        percentiles: ['#EBF8FF','#BEE3F8','#90CDF4','#63B3ED','#4299E1']
      },
      status: { success: '#48BB78', warning: '#ED8936', error: '#F56565', info: '#4299E1' }
    },
  },
  dark: {
    colors: {
      // Claude.ai inspired dark gray backgrounds (slightly lighter for warmth and readability)
      background: { primary: '#252525', secondary: '#2E2E2E', tertiary: '#363636' },
      // Soft beige text (warmer and softer than ivory)
      text: { primary: '#E8E3D3', secondary: '#D8D3C8', accent: '#E8E3D3', muted: '#9CA3AF' },
      // Burnt ember orange for buttons (Claude.ai style)
      ui: { primary: '#A85A39', secondary: '#B8674A', accent: '#C97A56', border: '#3A3A3A' },
      // Dark mode optimized visualization palette
      visualization: {
        primary: '#63B3ED', secondary: '#68D391', tertiary: '#F6AD55', quaternary: '#B794F4', quintary: '#4FD1C7',
        percentiles: ['#2D3748','#4A5568','#718096','#90CDF4','#63B3ED']
      },
      status: { success: '#68D391', warning: '#F6AD55', error: '#FC8181', info: '#63B3ED' }
    },
  },
  typography: {
    // Anthropic-style: Modern sans-serif with system font fallbacks
    fontFamily: { 
      primary: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif", 
      secondary: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif" 
    },
    fontWeight: { light: 300, regular: 400, medium: 500, semibold: 600, bold: 700 },
    // Generous line heights for readability
    lineHeight: { tight: 1.3, base: 1.6, relaxed: 1.8 },
  },
  // More generous spacing scale
  spacing: { xs: '0.5rem', sm: '0.75rem', md: '1.5rem', lg: '2.5rem', xl: '4rem', xxl: '6rem' },
  // Subtle, modern border radius
  borderRadius: { sm: '4px', md: '6px', lg: '8px', xl: '12px', full: '9999px' },
  // Minimal, soft shadows
  boxShadow: {
    light: { 
      sm: '0 1px 2px rgba(0, 0, 0, 0.04)', 
      md: '0 2px 4px rgba(0, 0, 0, 0.04)', 
      lg: '0 4px 8px rgba(0, 0, 0, 0.04)', 
      xl: '0 8px 16px rgba(0, 0, 0, 0.04)' 
    },
    dark: { 
      sm: '0 1px 2px rgba(0, 0, 0, 0.5)', 
      md: '0 2px 4px rgba(0, 0, 0, 0.5)', 
      lg: '0 4px 8px rgba(0, 0, 0, 0.5)', 
      xl: '0 8px 16px rgba(0, 0, 0, 0.5)' 
    },
  },
};

theme.header = {
  light: {
    // Minimal header: same as cards (tertiary ivory)
    gradientStart: '#F5F5E8', gradientEnd: '#F5F5E8',
    title: { color: '#1A1A1A', strokeWidth: '0px', strokeColor: 'transparent', textShadow: 'none' }
  },
  dark: {
    // Dark mode header: same as cards (tertiary dark gray)
    gradientStart: '#363636', gradientEnd: '#363636',
    title: { color: '#E8E3D3', strokeWidth: '0px', strokeColor: 'transparent', textShadow: 'none' }
  }
};

export const getThemeColors = (colorScheme: ColorScheme = 'light'): ThemeColors => theme[colorScheme]?.colors || theme.light.colors;
export const getBoxShadow = (colorScheme: ColorScheme = 'light') => theme.boxShadow[colorScheme] || theme.boxShadow.light;

export default theme;
