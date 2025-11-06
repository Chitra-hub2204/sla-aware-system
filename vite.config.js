import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Replace the URL below with your Railway backend domain if different,
// or set BACKEND_URL in your environment to override.
const backend = process.env.BACKEND_URL || 'https://sla-aware-system-production.up.railway.app'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // any request your frontend makes to /api/* will be proxied to the backend
      '/api': {
        target: backend,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  },
  preview: {
    port: 5173
  }
})
