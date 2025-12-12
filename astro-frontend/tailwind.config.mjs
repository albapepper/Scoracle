/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Sport-specific colors
        nba: {
          primary: '#1d428a',
          secondary: '#c8102e',
        },
        nfl: {
          primary: '#013369',
          secondary: '#d50a0a',
        },
        football: {
          primary: '#326b3f',
          secondary: '#ffffff',
        },
      },
    },
  },
  plugins: [],
};
