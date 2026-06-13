import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  const API_TARGET = env.VITE_API_URL || 'http://127.0.0.1:8000'
  const WS_TARGET = env.VITE_WS_URL || 'ws://127.0.0.1:8000'

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': '/src',
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: API_TARGET,
          changeOrigin: true,
        },
        '/sse': {
          target: API_TARGET,
          changeOrigin: true,
        },
        '/ws': {
          target: WS_TARGET,
          changeOrigin: true,
          ws: true,
          rewrite: (path) => path.replace(/^\/ws/, ''),
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
    },
  }
})
