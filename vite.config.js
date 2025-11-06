import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// ✅ Clean production config for Vercel
// No proxy needed — frontend directly calls Railway backend using full URL in api.js

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',       // Vercel uses this as output
    sourcemap: false
  },
  server: {
    port: 5173,           // local dev port
    open: true
  },
  preview: {
    port: 5173
  }
})
