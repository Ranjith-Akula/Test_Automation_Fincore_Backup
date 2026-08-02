import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const uiPort = Number(process.env.UI_PORT || process.env.VITE_DEV_PORT || 3000)
const apiPort = Number(process.env.API_PORT || 4000)

export default defineConfig({
  plugins: [react()],
  server: {
    port: uiPort,
    strictPort: true,
    proxy: {
      '/api': {
        target: `http://localhost:${apiPort}`,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'build',
    sourcemap: false
  }
})
