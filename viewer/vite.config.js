import { defineConfig } from 'vite';
import { cpSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  server: {
    fs: {
      // Allow Vite dev server to serve files from the repo root (../characters/).
      allow: ['..'],
    },
  },
  plugins: [
    {
      name: 'copy-characters',
      // After production build, copy characters/ into dist/ so the deployed
      // site can serve them at /characters/student_texting_walk.fbx.
      closeBundle() {
        try {
          cpSync(
            path.resolve(__dirname, '../characters'),
            path.resolve(__dirname, 'dist/characters'),
            { recursive: true }
          );
          console.log('Copied characters/ to dist/characters/');
        } catch (e) {
          console.warn('No characters folder to copy:', e.message);
        }
      },
    },
  ],
});
