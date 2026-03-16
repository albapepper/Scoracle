import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import compress from 'astro-compress';

const isDev = process.env.NODE_ENV === 'development' || process.argv.includes('dev');

// https://astro.build/config
export default defineConfig({
  // Site URL — reads from env for Railway
  site: process.env.SITE_URL || 'https://scoracle.up.railway.app',

  // Static by default; pages opt into SSR with `export const prerender = false`
  // In Astro 5+, this is the default behavior when an adapter is present.
  output: 'static',

  // Node.js SSR adapter for Railway deployment
  adapter: node({
    mode: 'standalone',
  }),

  build: {
    format: 'directory',
  },

  integrations: [
    // Only compress in production
    ...(!isDev ? [compress()] : []),
  ],

  vite: {
    define: {
      __DATA_VERSION__: JSON.stringify(Date.now().toString()),
    },
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
