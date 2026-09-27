import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

const proxyTarget = process.env.VITE_API_TARGET ?? 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // Any /api/* and /uploads,/pages,/reports static mounts fall through
      // to FastAPI so the demo needs no CORS friction in dev.
      '/api': { target: proxyTarget, changeOrigin: true },
      // Backend mounts: /static/uploads, /static/pages, /static/reports
      '/static': { target: proxyTarget, changeOrigin: true },
    },
  },
  build: {
    chunkSizeWarningLimit: 1200,
  },
})