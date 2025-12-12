import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';
import compress from 'astro-compress';

// https://astro.build/config
export default defineConfig({
  // Set your site URL for proper canonical URLs and SEO
  site: 'https://scoracle.vercel.app',
  
  // Pure static output - no server-side rendering needed
  // All entity data is fetched client-side via islands
  output: 'static',
  
  // Optimize for production builds
  build: {
    format: 'directory',
  },
  
  integrations: [
    react(),
    tailwind({
      applyBaseStyles: false,
    }),
    // Compress HTML, CSS, JavaScript output
    compress(),
  ],
  
  vite: {
    ssr: {
      noExternal: ['@tabler/icons-react'],
    },
    // Optimize build output
    build: {
      minify: 'terser',
      cssMinify: true,
      rollupOptions: {
        output: {
          manualChunks: undefined,
        },
      },
    },
    // Improve dev performance on Windows
    server: {
      middlewareMode: false,
    },
  },
});
