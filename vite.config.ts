import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'node:path';

/* Builds the React islands into static/dist/, where Django's staticfiles
   already looks. Fixed filenames (no content hash) so templates can point at
   {% static 'dist/adorn.js' %} without a manifest lookup. */
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    /* motion-primitives components import from '@/…' — the CLI drops them in
       components/motion-primitives/, so '@' is the repo root. */
    alias: { '@': resolve(import.meta.dirname, '.') },
  },
  build: {
    outDir: 'static/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(import.meta.dirname, 'frontend/main.tsx'),
      output: {
        entryFileNames: 'adorn.js',
        assetFileNames: 'adorn.[ext]',
      },
    },
  },
});
