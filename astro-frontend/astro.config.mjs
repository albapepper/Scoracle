import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import compress from 'astro-compress';

const isDev = process.env.NODE_ENV === 'development' || process.argv.includes('dev');

// https://astro.build/config
export default defineConfig({
  // Set your site URL for proper canonical URLs and SEO
  site: 'https://scoracle.vercel.app',
  
  // Pure static output - no server-side rendering needed
  output: 'static',
  
  build: {
    format: 'directory',
  },
  
  integrations: [
    // No React needed! All components are pure Astro with vanilla JS
    tailwind({
      applyBaseStyles: false,
    }),
    // Only compress in production
    ...(!isDev ? [compress()] : []),
  ],
  
  vite: {
    build: {
      minify: 'terser',
      cssMinify: true,
    },
  },
});
