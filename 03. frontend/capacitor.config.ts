import type { CapacitorConfig } from '@capacitor/cli'

/**
 * App móvil de AllpaShift (Capacitor 6: compila con Java 17).
 * Los archivos web van DENTRO de la app (build "mobile": `npm run build:mobile`) y la app llama a la
 * API Java del servidor (VITE_API_URL en .env.mobile). Regla 1 del doc 29: el móvil solo habla con /api/.
 */
const config: CapacitorConfig = {
  appId: 'com.allpashift.app',
  appName: 'AllpaShift',
  webDir: 'dist',
  backgroundColor: '#0f2a1f',
  android: {
    // La API del VPS todavía es http:// (HTTPS con Cloudflare queda pendiente)
    allowMixedContent: true,
  },
  ios: {
    contentInset: 'never',
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2500,
      launchAutoHide: false,
      backgroundColor: '#0f2a1f',
      showSpinner: false,
      androidScaleType: 'CENTER_CROP',
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#0f2a1f',
    },
  },
}

export default config
