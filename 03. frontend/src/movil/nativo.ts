/**
 * Comportamiento nativo de la app móvil (Android / iOS con Capacitor 6). En la web no hace nada.
 * - Barra de estado con el verde de AllpaShift y texto claro.
 * - Pantalla de inicio (splash): se oculta cuando la app ya está montada.
 * - Botón "atrás" de Android: vuelve a la pantalla anterior; en la portada sale de la app.
 */
import { App } from '@capacitor/app'
import { Capacitor } from '@capacitor/core'
import { SplashScreen } from '@capacitor/splash-screen'
import { StatusBar, Style } from '@capacitor/status-bar'
import type { Router } from 'vue-router'

const VERDE = '#0f2a1f'
/** Pantallas "raíz": desde aquí el botón atrás cierra la app en vez de navegar */
const RAICES = new Set(['/', '/hoy', '/bienvenida'])

export async function iniciarNativo(router: Router): Promise<void> {
  if (!Capacitor.isNativePlatform()) return

  try {
    await StatusBar.setStyle({ style: Style.Dark })
    if (Capacitor.getPlatform() === 'android') {
      await StatusBar.setBackgroundColor({ color: VERDE })
      await StatusBar.setOverlaysWebView({ overlay: false })
    }
  } catch {
    /* la barra de estado no es crítica */
  }

  App.addListener('backButton', ({ canGoBack }) => {
    const ruta = router.currentRoute.value.path
    if (RAICES.has(ruta) || !canGoBack) App.exitApp()
    else router.back()
  })

  // Ocultar la pantalla de inicio cuando ya se pintó la primera vista
  await router.isReady()
  setTimeout(() => SplashScreen.hide({ fadeOutDuration: 250 }).catch(() => {}), 200)
}
