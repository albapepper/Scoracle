/**
 * Theme configuration for Scoracle application
 * Using muted, sophisticated color palette to reduce eye strain
 */

const theme = {
  // Main color palette
  colors: {
    // Background colors
    background: {
      primary: '#f8f8f5', // Eggshell white for main background
      secondary: '#f2f2ee', // Slightly darker eggshell for cards/sections
      tertiary: '#e8e8e2', // For highlights and accents
    },
    
    // Text colors
    text: {
      primary: '#333333', // Dark gray for body text
      secondary: '#666666', // Medium gray for secondary text
      accent: '#3d4c53', // Deep slate blue-gray for headings
      muted: '#929292', // Muted gray for less important text
    },
    
    // UI element colors
    ui: {
      primary: '#546a7b', // Muted blue-slate for primary buttons and links
      secondary: '#728ca0', // Lighter blue-slate for secondary elements
      accent: '#879e7e', // Muted sage green for accents
      border: '#d9d9d6', // Light gray border color
    },

    // Data visualization colors - muted but distinct palette
    visualization: {
      primary: '#546a7b', // Main data point color
      secondary: '#879e7e', // Secondary data point color
      tertiary: '#a87d5f', // Terracotta for tertiary data
      quaternary: '#8b6d8a', // Muted lavender
      quintary: '#6a7a77', // Muted teal
      
      // For percentile indicators
      percentiles: [
        '#d8e2ec', // 0-20% (very low)
        '#b0c4d4', // 20-40% (below average)
        '#879eb8', // 40-60% (average)
        '#61799d', // 60-80% (above average)
        '#3d5680'  // 80-100% (elite)
      ]
    },
    
    // Status colors (more muted than standard)
    status: {
      success: '#879e7e', // Muted sage green
      warning: '#c9b178', // Muted amber
      error: '#b37264', // Muted rust red
      info: '#728ca0', // Muted blue
    }
  },
  
  // Typography
  typography: {
    fontFamily: {
      primary: "'Source Serif Pro', Georgia, serif", // Sophisticated serif font
      secondary: "'Source Sans Pro', 'Segoe UI', sans-serif", // Clean sans-serif font
    },
    fontWeight: {
      light: 300,
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.2,
      base: 1.5,
      relaxed: 1.8,
    }
  },
  
  // Spacing scale
  spacing: {
    xs: '0.25rem', // 4px
    sm: '0.5rem',  // 8px
    md: '1rem',    // 16px
    lg: '1.5rem',  // 24px
    xl: '2rem',    // 32px
    xxl: '3rem',   // 48px
  },
  
  // Border radius
  borderRadius: {
    sm: '0.125rem', // 2px
    md: '0.25rem',  // 4px
    lg: '0.5rem',   // 8px
    xl: '1rem',     // 16px
    full: '9999px', // Full rounded (circles)
  },
  
  // Box shadows - subtle for elegant feel
  boxShadow: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
    md: '0 2px 4px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.07)',
    lg: '0 4px 6px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.06)',
    xl: '0 10px 15px rgba(0, 0, 0, 0.03), 0 4px 6px rgba(0, 0, 0, 0.05)',
  }
};

export default theme;