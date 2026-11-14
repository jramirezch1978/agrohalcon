import { createRouter, createWebHashHistory } from 'vue-router'
import { useAppStore } from '@/stores/app'
import QuincenaView from '@/views/QuincenaView.vue'

declare module 'vue-router' {
  interface RouteMeta {
    titulo?: string
    sinNav?: boolean
    completa?: boolean
    /** La pantalla necesita una parcela elegida; si no hay, va al mapa */
    requiereParcela?: boolean
    /** Muestra el botón flotante del asistente */
    fabAsistente?: boolean
  }
}

// Hash history: funciona igual en web, PWA y dentro de Capacitor (Android)
export const router = createRouter({
  history: createWebHashHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', redirect: '/hoy' },
    { path: '/quincena', redirect: '/hoy' }, // ruta anterior
    { path: '/hoy', name: 'hoy', component: QuincenaView, meta: { titulo: 'inicio.titulo', requiereParcela: true, fabAsistente: true } },
    { path: '/mapa', name: 'mapa', component: () => import('@/views/MapView.vue'), meta: { titulo: 'mapa.titulo', completa: true } },
    { path: '/asistente', name: 'asistente', component: () => import('@/views/AssistantView.vue'), meta: { titulo: 'asistente.titulo', requiereParcela: true, completa: true } },
    { path: '/campana', name: 'campana', component: () => import('@/views/RotationsView.vue'), meta: { titulo: 'nav.campana', requiereParcela: true, fabAsistente: true } },
    { path: '/rotaciones', redirect: '/campana' }, // ruta anterior
    { path: '/validacion', name: 'validacion', component: () => import('@/views/ValidationView.vue'), meta: { titulo: 'validacion.titulo' } },
    { path: '/datos', name: 'datos', component: () => import('@/views/NasaDataView.vue'), meta: { titulo: 'datos.titulo' } },
    { path: '/bienvenida', name: 'bienvenida', component: () => import('@/views/OnboardingView.vue'), meta: { sinNav: true } },
    { path: '/:pathMatch(.*)*', redirect: '/hoy' },
  ],
})

router.beforeEach((to) => {
  const store = useAppStore()
  // Primera vez: mostrar la bienvenida
  if (!store.onboardingVisto && to.name !== 'bienvenida') return { name: 'bienvenida' }
  // Sin parcela elegida: elegirla en el mapa
  if (to.meta.requiereParcela && !store.parcela) return { name: 'mapa' }
})
