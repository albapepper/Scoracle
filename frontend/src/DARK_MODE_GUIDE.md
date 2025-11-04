# Dark Mode Implementation Guide

## Overview

Scoracle now features a beautiful, sophisticated dark mode designed with readability and user comfort in mind. The dark mode is inspired by the Claude mobile app, featuring deep muted grays that are easy on the eyes.

## Color Philosophy

### Light Mode
- **Background**: Eggshell white (#f8f8f5) - soft, readable background
- **Cards/Secondary**: Bone tone (#f3efe6) - subtle contrast from background
- **Text**: Dark gray (#333333) - high contrast, easy to read
- **UI Primary**: Muted blue-slate (#546a7b) - sophisticated accent color
- **Borders**: Light gray (#d9d9d6) - subtle visual structure

### Dark Mode
- **Background**: Deep muted gray (#1a1a18) - base color inspired by Claude app
- **Cards/Secondary**: Slightly darker (#242420) - creates visual hierarchy and card definition
- **Tertiary**: #2d2d29 - for highlights and subtle accents
- **Text**: Light gray (#e8e8e8) - comfortable contrast on dark backgrounds
- **UI Primary**: Lighter blue-slate (#8ab4d1) - better contrast on dark
- **Borders**: Dark gray (#3a3a36) - subtle structure on dark background

## How It Works

### Theme Configuration

The theme system is organized in `theme.js`:

```javascript
theme = {
  light: { colors: { ... } },  // Light mode palette
  dark: { colors: { ... } },   // Dark mode palette
  typography: { ... },         // Shared typography
  boxShadow: {
    light: { ... },           // Light mode shadows
    dark: { ... }             // Dark mode shadows (stronger for definition)
  },
  header: {
    light: { ... },           // Light mode header styling
    dark: { ... }             // Dark mode header styling
  }
}
```

### Using Colors in Components

All components should use the `useThemeMode()` hook and `getThemeColors()` helper:

```jsx
import { useThemeMode } from '../ThemeProvider';
import { getThemeColors } from '../theme';

function MyComponent() {
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);
  
  return (
    <div style={{ backgroundColor: colors.background.primary }}>
      <Text style={{ color: colors.text.primary }}>Hello</Text>
    </div>
  );
}
```

### Available Color Categories

Each color scheme has:

```javascript
colors: {
  background: {
    primary: '...',    // Main page background
    secondary: '...',  // Cards and panels
    tertiary: '...'    // Highlights and accents
  },
  text: {
    primary: '...',    // Body text
    secondary: '...',  // Secondary text
    accent: '...',     // Headings
    muted: '...'       // Less important text
  },
  ui: {
    primary: '...',    // Primary buttons and links
    secondary: '...',  // Secondary elements
    accent: '...',     // Accent colors
    border: '...'      // Border colors
  },
  visualization: {
    primary: '...',    // Charts and data viz
    secondary: '...',
    tertiary: '...',
    quaternary: '...',
    quintary: '...',
    percentiles: [...]  // For data percentiles
  },
  status: {
    success: '...',    // Success states
    warning: '...',    // Warning states
    error: '...',      // Error states
    info: '...'        // Info states
  }
}
```

## Toggling Dark Mode

Users can toggle dark mode via the settings drawer in the header:

1. Click the hamburger menu (☰) in the top-left
2. Click the "Settings" section
3. Toggle "Dark Mode" switch

The preference is saved to localStorage and restored on next visit.

## Box Shadows

Dark mode uses stronger shadows for better depth perception:

- **Light Mode**: Subtle shadows with low opacity (0.03-0.07)
- **Dark Mode**: Stronger shadows with higher opacity (0.2-0.4)

Always use the appropriate shadows:

```jsx
import theme, { getBoxShadow } from '../theme';

function MyCard() {
  const { colorScheme } = useThemeMode();
  const shadows = getBoxShadow(colorScheme);
  
  return (
    <div style={{ boxShadow: shadows.md }}>
      Content
    </div>
  );
}
```

## Mantine Integration

The theme is fully integrated with Mantine UI:

- `ThemeProvider` creates separate Mantine themes for light and dark modes
- All Mantine components (Button, Card, Paper, etc.) automatically use the correct colors
- Custom components should use `getThemeColors()` for consistency

## Adding New Components

When creating new components:

1. Import the theme hooks:
```jsx
import { useThemeMode } from '../ThemeProvider';
import { getThemeColors } from '../theme';
```

2. Get the current colors:
```jsx
const { colorScheme } = useThemeMode();
const colors = getThemeColors(colorScheme);
```

3. Use appropriate colors from the palette:
```jsx
// For backgrounds
backgroundColor: colors.background.primary  // or secondary/tertiary
// For text
color: colors.text.primary  // or secondary/accent/muted
// For UI elements
color: colors.ui.primary  // or secondary/accent
// For data visualization
fill: colors.visualization.primary
// For status
color: colors.status.success  // or warning/error/info
```

## API Sports Widget Theme

The API Sports widget is configured to match the current theme:
- Light mode → widget uses "white" theme
- Dark mode → widget uses "grey" theme

This is handled automatically in `ApiSportsConfig.jsx`.

## Accessibility Considerations

- All text has sufficient contrast (WCAG AA compliant)
- Dark mode uses slightly warmer/lighter colors for UI to ensure visibility
- Card separation is emphasized through color contrast
- No pure black/white combinations - all colors are muted for comfort

## Future Enhancements

Potential improvements:
- Custom color theme selector
- Per-component theme overrides
- System preference detection refinement
- Animation for theme transitions
- Export theme as CSS custom properties for wider use
