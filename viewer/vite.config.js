import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    fs: {
      // Allow Vite dev server to serve files from the repo root (../characters/).
      allow: ['..'],
    },
  },
});
