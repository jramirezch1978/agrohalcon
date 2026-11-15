<script setup lang="ts">
import type { MotivoUbicacion } from '@/services/ubicacion'
import { ArrowRight, Crosshair, Info, LoaderCircle, Map as IconoMapa, MapPin, Satellite, Search, X } from 'lucide-vue-next'
import { getCurrentInstance, h, onBeforeUnmount, onMounted, ref, render, shallowRef, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import MapLegend from '@/components/map/MapLegend.vue'
import ZonePopup from '@/components/map/ZonePopup.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import { ESTILO_RIESGO } from '@/composables/useRiesgo'
import { api } from '@/services/api'
import L, { iconoParcela } from '@/services/leaflet'
import { buscarLugar, nombreDeLugar, type LugarEncontrado } from '@/services/ubicacion'
import { PARCELA_PIURA, useAppStore } from '@/stores/app'
import type { ZonaRiesgo } from '@/types/api'

const store = useAppStore()
const router = useRouter()
const { t } = useI18n()
const appContext = getCurrentInstance()!.appContext

const contenedor = ref<HTMLDivElement>()
const mapa = shallowRef<L.Map>()
let marcador: L.Marker | undefined
const popupsMontados: HTMLElement[] = []

// ---------------------------------------------------------------------------
// Capa base: OpenStreetMap (por defecto) o imagen satelital de NASA GIBS (Blue Marble), ambas abiertas y sin clave
// ---------------------------------------------------------------------------
type Vista = 'mapa' | 'satelite'
const vista = ref<Vista>('mapa')
let capas: L.TileLayer[] = []

function crearCapas(v: Vista): L.TileLayer[] {
  if (v === 'mapa') {
    return [
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        className: 'capa-osm',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }),
    ]
  }
  // NASA GIBS: Blue Marble (composición sin nubes, siempre disponible) + nombres de lugares de GIBS.
  // Imágenes abiertas de la NASA, sin clave. Hasta zoom 8 de origen; más cerca se amplía.
  const GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best'
  return [
    L.tileLayer(`${GIBS}/BlueMarble_NextGeneration/default/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg`, {
      maxNativeZoom: 8,
      maxZoom: 18,
      attribution: 'Imagery: <a href="https://earthdata.nasa.gov/gibs">NASA GIBS</a> · Blue Marble (NASA Earth Observatory)',
    }),
    L.tileLayer(`${GIBS}/Reference_Labels_15m/default/default/GoogleMapsCompatible_Level13/{z}/{y}/{x}.png`, {
      maxNativeZoom: 13,
      maxZoom: 18,
      opacity: 0.9,
    }),
  ]
}

function ponerVista(v: Vista) {
  vista.value = v
  const m = mapa.value
  if (!m) return
  capas.forEach((c) => m.removeLayer(c))
  capas = crearCapas(v)
  capas.forEach((c) => c.addTo(m).bringToBack())
}

// ---------------------------------------------------------------------------
// "Mi parcela": punto tocado o ubicación del usuario
// ---------------------------------------------------------------------------
interface Punto {
  lat: number
  lon: number
  nombre?: string
  buscandoNombre: boolean
}
const punto = ref<Punto | null>(null)

function marcarParcela(lat: number, lon: number, nombre?: string) {
  const m = mapa.value
  if (!m) return
  m.closePopup()
  if (marcador) marcador.setLatLng([lat, lon])
  else {
    marcador = L.marker([lat, lon], { icon: iconoParcela(t('mapa.miParcela')), keyboard: false })
      .bindTooltip(t('mapa.miParcela'), { permanent: true, direction: 'top', className: 'zona-tooltip' })
      .addTo(m)
  }
  marcador.setTooltipContent(t('mapa.miParcela'))

  punto.value = { lat, lon, nombre, buscandoNombre: !nombre }
  if (!nombre) {
    nombreDeLugar(lat, lon, store.idioma).then((n) => {
      if (punto.value?.lat === lat && punto.value?.lon === lon) punto.value = { ...punto.value, nombre: n, buscandoNombre: false }
    })
  }
}

function quitarParcela() {
  punto.value = null
  marcador?.remove()
  marcador = undefined
}

/** Confirma la parcela: la guarda en Pinia y abre "¿Qué hago esta quincena?". */
function analizar(lat: number, lon: number, nombre?: string) {
  store.elegirParcela({ lat, lon, nombre })
  router.push('/hoy')
}

// ---------------------------------------------------------------------------
// Zonas de riesgo (GET /api/mapa?region=piura)
// ---------------------------------------------------------------------------
const errorZonas = ref(false)

/** Contenido del popup como componente Vue (con i18n), montado en un div para Leaflet. */
function contenidoPopup(z: ZonaRiesgo): HTMLElement {
  const el = document.createElement('div')
  const vnode = h(ZonePopup, { zona: z, onVer: () => analizar(z.lat, z.lon, `${z.nombre}, Piura`) })
  vnode.appContext = appContext
  render(vnode, el)
  popupsMontados.push(el)
  return el
}

async function dibujarZonas() {
  errorZonas.value = false
  try {
    const { zonas } = await api.getMapa('piura', store.idioma)
    const m = mapa.value
    if (!m) return
    for (const z of zonas) {
      const color = z.nivel ? ESTILO_RIESGO[z.nivel].hex : '#9ca3af'
      const etiqueta = z.nivel ? t(`riesgo.${z.nivel}`) : t('mapa.sinDato')
      // bubblingMouseEvents: false -> tocar una zona no dispara el clic del mapa (que marcaría "Mi parcela")
      L.circle([z.lat, z.lon], { radius: 11000, color, weight: 2.5, opacity: 0.95, fillColor: color, fillOpacity: 0.3, bubblingMouseEvents: false })
        .bindTooltip(`${z.nombre} · ${etiqueta}`, { className: 'zona-tooltip', direction: 'top', sticky: true })
        .bindPopup(() => contenidoPopup(z), { className: 'zona-popup', closeButton: true, autoPanPadding: [24, 120] })
        .addTo(m)
    }
  } catch {
    errorZonas.value = true
  }
}

// ---------------------------------------------------------------------------
// Buscador (Nominatim / OpenStreetMap)
// ---------------------------------------------------------------------------
const consulta = ref('')
const resultados = ref<LugarEncontrado[]>([])
const buscando = ref(false)
const sinResultados = ref(false)
let temporizador: number | undefined
let controlador: AbortController | undefined

/**
 * Política de uso de Nominatim: como máximo 1 petición por segundo y nada de autocompletar en cada tecla.
 * Se busca tras 1 s sin escribir, o al presionar Enter (respetando el segundo entre peticiones).
 */
const ESPERA_MS = 1000
let ultimaPeticion = 0

async function buscarAhora(q: string) {
  clearTimeout(temporizador)
  if (q.trim().length < 3) return
  const falta = ESPERA_MS - (Date.now() - ultimaPeticion)
  if (falta > 0) await new Promise((r) => setTimeout(r, falta))
  ultimaPeticion = Date.now()
  controlador?.abort()
  controlador = new AbortController()
  buscando.value = true
  try {
    resultados.value = await buscarLugar(q, store.idioma, controlador.signal)
    sinResultados.value = resultados.value.length === 0
  } catch {
    /* búsqueda cancelada o sin red */
  } finally {
    buscando.value = false
  }
}

watch(consulta, (q) => {
  clearTimeout(temporizador)
  sinResultados.value = false
  if (q.trim().length < 3) {
    resultados.value = []
    return
  }
  temporizador = window.setTimeout(() => buscarAhora(q), ESPERA_MS)
})

function alPresionarEnter() {
  if (resultados.value[0]) irA(resultados.value[0])
  else buscarAhora(consulta.value)
}

function irA(l: LugarEncontrado) {
  resultados.value = []
  consulta.value = ''
  ;(document.activeElement as HTMLElement | null)?.blur()
  mapa.value?.flyTo([l.lat, l.lon], 10, { duration: 1.2 })
  marcarParcela(l.lat, l.lon, [l.nombre, l.detalle.split(',').at(-1)?.trim()].filter(Boolean).join(', '))
}

// ---------------------------------------------------------------------------
// Usar mi ubicación
// ---------------------------------------------------------------------------
const avisoUbicacion = ref<'' | MotivoUbicacion>('')
let temporizadorAviso: number | undefined

async function usarMiUbicacion() {
  avisoUbicacion.value = ''
  const r = await store.pedirUbicacion()
  if (!r.ok) {
    avisoUbicacion.value = r.motivo
    clearTimeout(temporizadorAviso)
    temporizadorAviso = window.setTimeout(() => (avisoUbicacion.value = ''), 7000)
    return
  }
  mapa.value?.flyTo([r.coords.lat, r.coords.lon], 12, { duration: 1.2 })
  marcarParcela(r.coords.lat, r.coords.lon)
}

// ---------------------------------------------------------------------------
// Ciclo de vida
// ---------------------------------------------------------------------------
onMounted(() => {
  const inicio = store.parcela ?? PARCELA_PIURA
  const m = L.map(contenedor.value!, { zoomControl: false, worldCopyJump: true }).setView([inicio.lat, inicio.lon], 9)
  L.control.zoom({ position: 'bottomright' }).addTo(m)
  mapa.value = m
  ponerVista(vista.value)
  m.on('click', (e: L.LeafletMouseEvent) => marcarParcela(e.latlng.lat, e.latlng.lng))
  dibujarZonas()
  if (store.parcela) marcarParcela(store.parcela.lat, store.parcela.lon, store.parcela.nombre)
})

onBeforeUnmount(() => {
  clearTimeout(temporizador)
  clearTimeout(temporizadorAviso)
  controlador?.abort()
  popupsMontados.forEach((el) => render(null, el))
  mapa.value?.remove()
})
</script>

<template>
  <section class="relative h-[calc(100dvh-4rem-env(safe-area-inset-top))] lg:h-dvh">
    <h1 class="sr-only">{{ $t('mapa.titulo') }}</h1>
    <div ref="contenedor" class="absolute inset-0 z-0" role="application" :aria-label="$t('mapa.tocaMapa')" />

    <!-- Buscador -->
    <div class="absolute inset-x-3 top-3 z-[400] mx-auto max-w-xl lg:top-6">
      <div class="superficie flex items-center gap-2 !rounded-2xl px-4 shadow-float">
        <Search class="size-5 shrink-0 text-stone-400" aria-hidden="true" />
        <input
          v-model="consulta"
          type="search"
          enterkeyhint="search"
          :placeholder="$t('mapa.buscarLugar')"
          :aria-label="$t('mapa.buscarLugar')"
          class="h-14 min-w-0 flex-1 bg-transparent text-[16px] outline-none placeholder:text-stone-400"
          @keydown.enter="alPresionarEnter"
        />
        <LoaderCircle v-if="buscando" class="size-5 animate-spin text-stone-400" :aria-label="$t('mapa.buscando')" />
        <button v-else-if="consulta" type="button" :aria-label="$t('acciones.cerrar')" class="grid size-10 place-items-center rounded-full hover:bg-tinta/5 dark:hover:bg-white/8" @click="consulta = ''">
          <X class="size-4" aria-hidden="true" />
        </button>
      </div>
      <ul v-if="resultados.length || sinResultados" class="superficie mt-2 overflow-hidden !rounded-2xl shadow-float">
        <li v-if="sinResultados" class="px-4 py-3 text-sm text-stone-500">{{ $t('mapa.sinResultados') }}</li>
        <li v-for="r in resultados" :key="`${r.lat},${r.lon}`">
          <button type="button" class="flex min-h-14 w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-arena dark:hover:bg-white/5" @click="irA(r)">
            <MapPin class="size-4 shrink-0 text-agro-600 dark:text-brote-400" aria-hidden="true" />
            <span class="min-w-0">
              <span class="block truncate text-sm font-semibold">{{ r.nombre }}</span>
              <span class="block truncate text-xs text-stone-500">{{ r.detalle }}</span>
            </span>
          </button>
        </li>
      </ul>
    </div>

    <!-- Indicación inicial (abajo, donde luego aparece la tarjeta) -->
    <p
      v-if="!punto"
      class="pointer-events-none absolute inset-x-3 bottom-[calc(6.75rem+env(safe-area-inset-bottom))] z-[400] mx-auto flex w-fit items-center gap-2 rounded-full bg-tinta/90 px-4 py-2.5 text-sm font-semibold text-white shadow-float backdrop-blur lg:bottom-8"
    >
      <MapPin class="size-4 text-brote-300" aria-hidden="true" />{{ $t('mapa.tocaMapa') }}
    </p>

    <!-- Leyenda (esquina superior izquierda) -->
    <MapLegend class="absolute top-[5.5rem] left-3 z-[400] lg:top-28 lg:left-6" />

    <!-- Controles flotantes (esquina superior derecha) -->
    <div class="absolute top-[5.5rem] right-3 z-[400] flex flex-col items-end gap-2 lg:top-28 lg:right-6">
      <button
        type="button"
        class="flex min-h-12 items-center gap-2 rounded-2xl bg-agro-700 px-4 text-sm font-semibold text-white shadow-float transition hover:bg-agro-800 active:scale-95 disabled:opacity-80 dark:bg-brote-400 dark:text-tinta"
        :disabled="store.ubicando"
        @click="usarMiUbicacion"
      >
        <LoaderCircle v-if="store.ubicando" class="size-5 animate-spin" aria-hidden="true" />
        <Crosshair v-else class="size-5" aria-hidden="true" />
        <span>{{ store.ubicando ? $t('mapa.ubicando') : $t('acciones.usarUbicacion') }}</span>
      </button>
      <button
        type="button"
        :aria-label="vista === 'mapa' ? $t('mapa.capaSatelite') : $t('mapa.capaMapa')"
        :title="vista === 'mapa' ? $t('mapa.capaSatelite') : $t('mapa.capaMapa')"
        class="grid size-12 place-items-center rounded-2xl bg-white text-tinta shadow-float transition active:scale-95 dark:bg-noche-2 dark:text-white"
        @click="ponerVista(vista === 'mapa' ? 'satelite' : 'mapa')"
      >
        <Satellite v-if="vista === 'mapa'" class="size-5" aria-hidden="true" />
        <IconoMapa v-else class="size-5" aria-hidden="true" />
      </button>
    </div>

    <!-- Aviso amable si no hay permiso de ubicación -->
    <Transition enter-from-class="-translate-y-2 opacity-0" leave-to-class="opacity-0" enter-active-class="transition duration-300" leave-active-class="transition duration-200">
      <div v-if="avisoUbicacion" role="alert" class="absolute inset-x-3 top-[13rem] z-[450] mx-auto flex max-w-md items-start gap-3 rounded-2xl bg-white p-4 text-sm shadow-float ring-1 ring-amber-300 lg:top-60 dark:bg-noche-2 dark:ring-amber-400/40">
        <Info class="mt-0.5 size-5 shrink-0 text-amber-600 dark:text-amber-300" aria-hidden="true" />
        <p class="flex-1">{{ $t(`mapa.aviso.${avisoUbicacion}`) }}</p>
        <button type="button" :aria-label="$t('acciones.cerrar')" class="-m-1 grid size-8 place-items-center rounded-full hover:bg-tinta/5" @click="avisoUbicacion = ''">
          <X class="size-4" aria-hidden="true" />
        </button>
      </div>
    </Transition>

    <!-- Tarjeta inferior: "Mi parcela" -->
    <Transition enter-from-class="translate-y-6 opacity-0" leave-to-class="translate-y-6 opacity-0" enter-active-class="transition duration-300" leave-active-class="transition duration-200">
      <div v-if="punto" class="absolute inset-x-3 bottom-[calc(6.5rem+env(safe-area-inset-bottom))] z-[450] mx-auto max-w-md lg:bottom-6">
        <div class="superficie p-4 shadow-float">
          <div class="flex items-start gap-3">
            <span class="grid size-11 shrink-0 place-items-center rounded-2xl bg-tinta text-brote-300 dark:bg-brote-400 dark:text-tinta">
              <MapPin class="size-5" aria-hidden="true" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="text-[11px] font-bold tracking-[0.12em] text-stone-500 uppercase">{{ $t('mapa.miParcela') }}</p>
              <p class="truncate font-display text-lg font-bold tracking-tight">
                <span v-if="punto.buscandoNombre" class="inline-block h-5 w-32 animate-pulse rounded bg-tinta/8 align-middle dark:bg-white/10" />
                <template v-else>{{ punto.nombre ?? $t('mapa.puntoElegido') }}</template>
              </p>
              <p class="text-xs text-stone-500 tabular-nums dark:text-stone-400">
                {{ $t('mapa.coordenadas') }}: {{ punto.lat.toFixed(4) }}, {{ punto.lon.toFixed(4) }}
              </p>
            </div>
            <button type="button" :aria-label="$t('acciones.cerrar')" class="grid size-10 place-items-center rounded-full hover:bg-tinta/5 dark:hover:bg-white/8" @click="quitarParcela">
              <X class="size-4" aria-hidden="true" />
            </button>
          </div>
          <BaseButton class="mt-4" bloque :icono-derecha="ArrowRight" @click="analizar(punto.lat, punto.lon, punto.nombre)">
            {{ $t('acciones.analizarParcela') }}
          </BaseButton>
        </div>
      </div>
    </Transition>
  </section>
</template>
