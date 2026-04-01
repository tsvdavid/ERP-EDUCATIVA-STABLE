import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

console.log('--- VITE PROXY DESTINATION IS: ---', process.env.VITE_API_URL_PROXY || process.env.API_PROXY_TARGET || 'http://backend:8000');

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    dedupe: ['react', 'react-dom']
  },
  server: {
    allowedHosts: true,
    host: true,
    port: 5173,
    strictPort: true,
    // Add HMR config for Cloudflare Tunnels (prevents blank screens from wss crashes)
    hmr: {
      protocol: 'wss',
      clientPort: 443, // Force WSS over 443 for HTTPS tunnels
      path: 'vite-hmr' // Avoid conflict with Django channels
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL_PROXY || process.env.API_PROXY_TARGET || 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/media': {
        target: process.env.VITE_API_URL_PROXY || process.env.API_PROXY_TARGET || 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
