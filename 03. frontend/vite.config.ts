import { fileURLToPath, URL } from 'node:url'
import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

/**
 * Escribe precache.json con TODOS los archivos del build (JS de cada pantalla, CSS, fuentes, íconos).
 * El service worker los guarda al instalarse: la app abre cualquier pantalla sin internet aunque nunca se haya visitado.
 */
function precache(): Plugin {
  return {
    name: 'allpashift-precache',
    apply: 'build',
    generateBundle(_, bundle) {
      const archivos = Object.keys(bundle).filter((f) => !f.endsWith('.map') && f !== 'precache.json')
      this.emitFile({ type: 'asset', fileName: 'precache.json', source: JSON.stringify(archivos.map((f) => `./${f}`)) })
    },
  }
}

export default defineConfig({
  plugins: [vue(), tailwindcss(), precache()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: { host: true, port: 5173 },
})
