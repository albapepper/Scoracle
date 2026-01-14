import { defineConfig } from 'astro/config';
import compress from 'astro-compress';

const isDev = process.env.NODE_ENV === 'development' || process.argv.includes('dev');

// https://astro.build/config
export default defineConfig({
  // Set your site URL for proper canonical URLs and SEO
  site: 'https://scoracle.vercel.app',

  // Hybrid output - static by default, SSR for dynamic pages
  output: 'hybrid',

  build: {
    format: 'directory',
  },

  integrations: [
    // Only compress in production
    ...(!isDev ? [compress()] : []),
  ],

  vite: {
    build: {
      minify: 'terser',
      cssMinify: true,
      // Drop console.log in production for smaller bundle
      terserOptions: {
        compress: {
          drop_console: !isDev,
        },
      },
    },
  },
});
