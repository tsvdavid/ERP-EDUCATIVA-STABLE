import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

console.log('--- VITE PROXY DESTINATION IS: ---', process.env.VITE_API_URL_PROXY || process.env.API_PROXY_TARGET || 'http://localhost:8000');

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  base: '/',
  // Proxy only (no HMR, no host overrides)
  server: {
    allowedHosts: [
      'eduka360.tecnoval.com.ec',
      'localhost',
      '127.0.0.1',
    ],
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL_PROXY || process.env.API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/media': {
        target: process.env.VITE_API_URL_PROXY || process.env.API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  }
})
