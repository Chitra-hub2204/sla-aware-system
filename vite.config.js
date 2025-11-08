import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// ✅ Clean production config for Netlify
// Uses base: "./" for proper relative asset paths
// Backend URL is handled via environment variable in api.js (VITE_API_BASE_URL)

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'dist',      // Netlify uses this as the publish directory
    sourcemap: false
  },
  server: {
    port: 5173,
    open: true
  },
  preview: {
    port: 5173
  }
})
