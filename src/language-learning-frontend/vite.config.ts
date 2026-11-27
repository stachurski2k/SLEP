import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/model-service': {
        target: 'http://localhost:5001',
        rewrite: (path) => path.replace(/^\/model-service/, ''),
      },
    },
  },
})
