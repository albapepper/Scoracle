# Anthropic-Inspired Theme Proposal for Scoracle

## Design Philosophy

This theme is inspired by Anthropic's aesthetic: **clean, minimal, highly readable, and data-centric**. The design prioritizes:

1. **Typography Excellence**: Large, readable fonts with generous line spacing
2. **High Contrast**: Strong contrast ratios for accessibility and readability
3. **Generous White Space**: Breathing room for content and data visualizations
4. **Subtle Elegance**: Minimal use of color, letting content shine
5. **Modern Sans-Serif**: Clean, professional typeface

## Key Design Elements

### Color Palette

**Light Mode:**
- **Background**: Pure white (#FFFFFF) with subtle off-whites for depth
- **Text**: Deep charcoal (#1A1A1A) for primary text, medium gray (#666666) for secondary
- **Accents**: Subtle blue-gray (#4A5568) for UI elements
- **Data Visualization**: Carefully curated palette that's both accessible and visually distinct

**Dark Mode:**
- **Background**: Deep charcoal (#0F0F0F) with slightly lighter grays for depth
- **Text**: Soft white (#F5F5F5) for primary, light gray (#B8B8B8) for secondary
- **Accents**: Muted blue-gray (#718096) for UI elements
- **Data Visualization**: Dark mode optimized palette with maintained contrast

### Typography

- **Primary Font**: Inter (or system font stack: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif)
- **Monospace**: 'SF Mono', 'Monaco', 'Cascadia Code', monospace for code/data
- **Font Sizes**: Generous sizing with clear hierarchy
- **Line Height**: 1.6-1.8 for optimal readability
- **Letter Spacing**: Slightly increased for body text (-0.01em to -0.02em)

### Spacing & Layout

- **Container Max Width**: 1280px (wider than current for data tables/charts)
- **Generous Padding**: 2rem-3rem on desktop, 1rem on mobile
- **Section Spacing**: 4rem-6rem between major sections
- **Card Padding**: 1.5rem-2rem

### Visual Elements

- **Borders**: Subtle, thin (1px) with low opacity
- **Shadows**: Minimal, soft shadows for depth
- **Radius**: Small border radius (4-8px) for modern feel
- **Gradients**: Very subtle, if used at all

## Implementation Strategy

1. Update theme tokens with new color palette
2. Enhance typography system with Inter font
3. Adjust spacing scale for more generous whitespace
4. Update component styles to match Anthropic aesthetic
5. Ensure high contrast ratios (WCAG AAA where possible)

## Font Loading

We'll use Inter from Google Fonts or a CDN, with system font fallbacks for performance.

