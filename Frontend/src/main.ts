import { Capacitor } from '@capacitor/core'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { router } from './router'
import { i18n } from './i18n'
import './assets/main.css'

const app = createApp(App)
app.use(createPinia()) // antes del router: el guard usa el store
app.use(i18n)
app.use(router)
app.mount('#app')

// PWA: service worker solo en producción (en desarrollo interfiere con la recarga en caliente)
// En Android (Capacitor) los archivos ya están dentro del APK: no hace falta
if (import.meta.env.PROD && !Capacitor.isNativePlatform() && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('./sw.js').catch(() => {}))
}
