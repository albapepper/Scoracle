/**
 * Theme configuration for Scoracle application
 * Using muted, sophisticated color palette to reduce eye strain
 * Includes both light and dark modes with accessible contrast
 * 
 * Dark Mode Philosophy:
 * - Background: Deep muted gray (#1a1a18) inspired by Claude's mobile app
 * - Cards: Slightly darker (#242420) for visual hierarchy and card definition
 * - Text: Light gray (#e8e8e8) for comfortable readability on dark backgrounds
 * - UI Elements: Lighter, warmer colors for good contrast and visual pop
 * - Overall: Maintains sophisticated, accessible design focused on readability
 */

const theme = {
  // Main color palette - LIGHT MODE
  light: {
    colors: {
      // Background colors
      background: {
        primary: '#f8f8f5', // Eggshell white for main page background
        secondary: '#f3efe6', // Bone tone for cards/sections (softer than eggshell)
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
  },

  // DARK MODE - Muted deep gray inspired by Claude mobile app
  dark: {
    colors: {
      // Background colors - Muted deep grays for easy on the eyes
      background: {
        primary: '#222220', // Main dark background - slightly lighter muted gray
        secondary: '#2a2a27', // Cards/sections - slightly darker than main background
        tertiary: '#323230', // Highlights and accents - subtle lift from secondary
      },
      
      // Text colors
      text: {
        primary: '#e8e8e8', // Light gray for body text
        secondary: '#b8b8b8', // Medium gray for secondary text
        accent: '#d4dce1', // Light blue-gray for headings
        muted: '#7a7a7a', // Muted gray for less important text
      },
      
      // UI element colors
      ui: {
        primary: '#8ab4d1', // Lighter blue-slate for buttons (good contrast on dark)
        secondary: '#6d96b8', // Secondary blue-slate
        accent: '#a8c98a', // Muted sage green for accents
        border: '#3a3a36', // Dark gray border color
      },

      // Data visualization colors
      visualization: {
        primary: '#8ab4d1', // Main data point color
        secondary: '#a8c98a', // Secondary data point color
        tertiary: '#d4a876', // Terracotta for tertiary data
        quaternary: '#c9afc9', // Muted lavender
        quintary: '#95a9a5', // Muted teal
        
        // For percentile indicators
        percentiles: [
          '#3a4452', // 0-20% (very low)
          '#4a5f73', // 20-40% (below average)
          '#5a7a94', // 40-60% (average)
          '#7a9bb5', // 60-80% (above average)
          '#8ab4d1'  // 80-100% (elite)
        ]
      },
      
      // Status colors
      status: {
        success: '#a8c98a', // Muted sage green
        warning: '#d4b876', // Muted amber
        error: '#d4876a', // Muted rust red
        info: '#8ab4d1', // Muted blue
      }
    },
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
    light: {
      sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
      md: '0 2px 4px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.07)',
      lg: '0 4px 6px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.06)',
      xl: '0 10px 15px rgba(0, 0, 0, 0.03), 0 4px 6px rgba(0, 0, 0, 0.05)',
    },
    dark: {
      sm: '0 1px 3px rgba(0, 0, 0, 0.3)',
      md: '0 2px 6px rgba(0, 0, 0, 0.3), 0 1px 3px rgba(0, 0, 0, 0.2)',
      lg: '0 4px 12px rgba(0, 0, 0, 0.4), 0 2px 4px rgba(0, 0, 0, 0.2)',
      xl: '0 10px 20px rgba(0, 0, 0, 0.4), 0 4px 8px rgba(0, 0, 0, 0.2)',
    }
  },
};

// Header-specific tokens for consistent styling
theme.header = {
  light: {
    // Deeper, sophisticated blue gradient
    gradientStart: '#2b6fb4',
    gradientEnd: '#1e5aa0',
    title: {
      color: '#ffffff',
      strokeWidth: '1.25px',
      strokeColor: 'rgba(0,0,0,0.9)',
      textShadow: '0 0 1px rgba(0,0,0,0.6), 0 1px 0 rgba(0,0,0,0.6)'
    }
  },
  dark: {
    // Muted gradient for dark mode
    gradientStart: '#2d3f4f',
    gradientEnd: '#1f2d39',
    title: {
      color: '#e8e8e8',
      strokeWidth: '0.5px',
      strokeColor: 'rgba(0,0,0,0.3)',
      textShadow: '0 1px 2px rgba(0,0,0,0.5)'
    }
  }
};

// Helper function to get theme colors based on color scheme
export const getThemeColors = (colorScheme = 'light') => {
  return theme[colorScheme]?.colors || theme.light.colors;
};

// Helper function to get box shadows based on color scheme
export const getBoxShadow = (colorScheme = 'light') => {
  return theme.boxShadow[colorScheme] || theme.boxShadow.light;
};

export default theme;