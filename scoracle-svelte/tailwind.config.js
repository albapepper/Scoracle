import { join } from 'path';
import { skeleton } from '@skeletonlabs/tw-plugin';

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './src/**/*.{html,js,svelte,ts}',
    join(require.resolve('@skeletonlabs/skeleton'), '../**/*.{html,js,svelte,ts}'),
  ],
  theme: {
    extend: {
      colors: {
        // Scoracle custom colors from React theme
        'scoracle': {
          // Light mode
          'bg-primary': '#F5F5E8',
          'bg-secondary': '#EAEADA',
          'bg-tertiary': '#E0E0D0',
          'text-primary': '#2D3748',
          'text-secondary': '#4A5568',
          'text-accent': '#1A365D',
          'ui-primary': '#2D3748',
          'ui-border': '#CBD5E0',
          // Dark mode
          'dark-bg-primary': '#1A1A1A',
          'dark-bg-secondary': '#242424',
          'dark-bg-tertiary': '#2D2D2D',
          'dark-text-primary': '#F5F5E8',
          'dark-text-secondary': '#D0D0C0',
          'dark-text-accent': '#E8C4A0',
          'dark-ui-primary': '#A85A39',
          'dark-ui-border': '#404040',
        },
      },
      fontFamily: {
        sans: ['Söhne', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    skeleton({
      themes: {
        custom: [
          {
            name: 'scoracle-light',
            properties: {
              // Surface colors
              '--color-surface-50': '#F5F5E8',
              '--color-surface-100': '#EAEADA',
              '--color-surface-200': '#E0E0D0',
              '--color-surface-300': '#D0D0C0',
              '--color-surface-400': '#B0B0A0',
              '--color-surface-500': '#909080',
              '--color-surface-600': '#707060',
              '--color-surface-700': '#505040',
              '--color-surface-800': '#303020',
              '--color-surface-900': '#1A1A10',
              // Primary colors
              '--color-primary-50': '#F7FAFC',
              '--color-primary-100': '#EDF2F7',
              '--color-primary-200': '#E2E8F0',
              '--color-primary-300': '#CBD5E0',
              '--color-primary-400': '#A0AEC0',
              '--color-primary-500': '#2D3748',
              '--color-primary-600': '#2D3748',
              '--color-primary-700': '#1A202C',
              '--color-primary-800': '#171923',
              '--color-primary-900': '#0D0D0D',
              // Text
              '--theme-font-color-base': '#2D3748',
              '--theme-font-color-dark': '#F5F5E8',
            },
          },
          {
            name: 'scoracle-dark',
            properties: {
              // Surface colors (dark)
              '--color-surface-50': '#404040',
              '--color-surface-100': '#363636',
              '--color-surface-200': '#2D2D2D',
              '--color-surface-300': '#242424',
              '--color-surface-400': '#1A1A1A',
              '--color-surface-500': '#141414',
              '--color-surface-600': '#0D0D0D',
              '--color-surface-700': '#0A0A0A',
              '--color-surface-800': '#050505',
              '--color-surface-900': '#000000',
              // Primary colors (burnt ember orange for dark)
              '--color-primary-50': '#F9AE82',
              '--color-primary-100': '#E99D73',
              '--color-primary-200': '#D98C64',
              '--color-primary-300': '#C97A56',
              '--color-primary-400': '#B8674A',
              '--color-primary-500': '#A85A39',
              '--color-primary-600': '#8F563D',
              '--color-primary-700': '#7D4A33',
              '--color-primary-800': '#6B3F2A',
              '--color-primary-900': '#5A3422',
              // Text
              '--theme-font-color-base': '#F5F5E8',
              '--theme-font-color-dark': '#2D3748',
            },
          },
        ],
      },
    }),
  ],
};

