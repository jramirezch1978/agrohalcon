import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // Igual que nginx.conf: ERDDAP (MUR SST) no permite CORS
      '/nasa/erddap': { target: 'https://coastwatch.pfeg.noaa.gov', changeOrigin: true, rewrite: (p) => p.replace(/^\/nasa\/erddap/, '/erddap') },
      '/api': { target: 'http://2.29.101.199', changeOrigin: true },
    },
  },
})
