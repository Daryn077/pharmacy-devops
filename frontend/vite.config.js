import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Для локальной разработки (npm run dev) запросы проксируются так же, как это делает Gateway:
// /api/pharmacy/* -> backend :8000, /api/delivery/* -> delivery-service :8001 (префикс удаляется)
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/pharmacy': {
        target: 'http://localhost:8000',
        rewrite: (p) => p.replace(/^\/api\/pharmacy/, ''),
      },
      '/api/delivery': {
        target: 'http://localhost:8001',
        rewrite: (p) => p.replace(/^\/api\/delivery/, ''),
      },
    },
  },
})
