import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { i18n, type Idioma } from '@/i18n'
import { api, ApiError, MODO } from '@/services/api'
import { useOrigenStore } from '@/stores/origen'
import type { ClaveIndicador, CultivoPermanente, MesISO, NivelRiesgo, OpcionesRecomendacion, Recomendacion, TipoCultivo } from '@/types/api'
import { ErrorUbicacion, nombreDeLugar, obtenerUbicacion, type Coordenadas, type MotivoUbicacion } from '@/services/ubicacion'

export interface Parcela {
  lat: number
  lon: number
  nombre?: string
}

export type Tema = 'claro' | 'oscuro'
export type EstadoCarga = 'inicial' | 'cargando' | 'listo' | 'error'
export type ResultadoUbicacion = { ok: true; coords: Coordenadas } | { ok: false; motivo: MotivoUbicacion }

const CLAVES = {
  parcela: 'allpashift:parcela',
  recomendacion: 'allpashift:ultimaRecomendacion',
  idioma: 'allpashift:idioma',
  tema: 'allpashift:tema',
  onboarding: 'allpashift:onboardingVisto',
  cultivo: 'allpashift:miCultivo',
}

/** Mes "AAAA-MM" a n meses de hoy */
export function mesDesdeHoy(n: number): MesISO {
  const d = new Date()
  const f = new Date(d.getFullYear(), d.getMonth() + n, 1)
  return `${f.getFullYear()}-${String(f.getMonth() + 1).padStart(2, '0')}`
}

interface MiCultivo {
  tipo: TipoCultivo
  permanente: CultivoPermanente
  /** Mes de siembra: 0 = este mes, 1 = el próximo, 2 = en 2 meses */
  mesSiembraOffset: 0 | 1 | 2
}

/** Vista inicial de la demo */
export const PARCELA_PIURA: Parcela = { lat: -5.19, lon: -80.63, nombre: 'Piura, Perú' }

function leer<T>(clave: string): T | null {
  try {
    const raw = localStorage.getItem(clave)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}
function guardar(clave: string, valor: unknown) {
  try {
    localStorage.setItem(clave, JSON.stringify(valor))
  } catch {
    /* modo privado o almacenamiento lleno: la app sigue funcionando */
  }
}

export const useAppStore = defineStore('app', () => {
  // --- Parcela seleccionada (null hasta que el usuario la elige) ---
  const parcela = ref<Parcela | null>(leer<Parcela>(CLAVES.parcela))
  watch(parcela, (p) => guardar(CLAVES.parcela, p), { deep: true })

  const redondear4 = (n: number) => Math.round(n * 1e4) / 1e4

  function elegirParcela(p: Parcela) {
    const nueva = { ...p, lat: redondear4(p.lat), lon: redondear4(p.lon) }
    parcela.value = nueva
    // Completar el nombre del lugar en segundo plano si no vino
    if (!nueva.nombre) {
      nombreDeLugar(nueva.lat, nueva.lon, idioma.value).then((nombre) => {
        const actual = parcela.value
        if (nombre && actual && actual.lat === nueva.lat && actual.lon === nueva.lon) parcela.value = { ...nueva, nombre }
      })
    }
  }

  /** Pide la ubicación del dispositivo (no cambia la parcela: eso lo decide la pantalla). */
  const ubicando = ref(false)
  async function pedirUbicacion(): Promise<ResultadoUbicacion> {
    ubicando.value = true
    try {
      const { lat, lon } = await obtenerUbicacion()
      return { ok: true, coords: { lat: redondear4(lat), lon: redondear4(lon) } }
    } catch (e) {
      return { ok: false, motivo: e instanceof ErrorUbicacion ? e.motivo : 'error' }
    } finally {
      ubicando.value = false
    }
  }

  // --- Idioma ---
  const idioma = ref<Idioma>(i18n.global.locale.value as Idioma)
  watch(
    idioma,
    (l) => {
      i18n.global.locale.value = l
      document.documentElement.lang = l
      try {
        localStorage.setItem(CLAVES.idioma, l)
      } catch {
        /* ignorar */
      }
    },
    { immediate: true },
  )

  // --- Tema claro / oscuro ---
  const tema = ref<Tema>(document.documentElement.classList.contains('dark') ? 'oscuro' : 'claro')
  watch(
    tema,
    (t) => {
      document.documentElement.classList.toggle('dark', t === 'oscuro')
      document.querySelector('meta[name="theme-color"]')?.setAttribute('content', t === 'oscuro' ? '#08110d' : '#f3f1ea')
      try {
        localStorage.setItem(CLAVES.tema, t)
      } catch {
        /* ignorar */
      }
    },
    { immediate: true },
  )
  const alternarTema = () => (tema.value = tema.value === 'oscuro' ? 'claro' : 'oscuro')

  // --- Onboarding ---
  const onboardingVisto = ref<boolean>(leer<boolean>(CLAVES.onboarding) ?? false)
  function completarOnboarding() {
    onboardingVisto.value = true
    guardar(CLAVES.onboarding, true)
  }

  // --- Mi cultivo: temporal (voy a sembrar) o permanente (mango, limón, banano) ---
  const miCultivo = ref<MiCultivo>({ tipo: 'temporal', permanente: 'mango', mesSiembraOffset: 1, ...(leer<Partial<MiCultivo>>(CLAVES.cultivo) ?? {}) })
  watch(miCultivo, (c) => guardar(CLAVES.cultivo, c), { deep: true })
  const tipoCultivo = computed(() => miCultivo.value.tipo)
  const mesSiembra = computed(() => mesDesdeHoy(miCultivo.value.mesSiembraOffset))

  /** Parámetros para /api/recomendacion y /api/asistente */
  const opcionesCultivo = computed<OpcionesRecomendacion>(() =>
    miCultivo.value.tipo === 'permanente'
      ? { tipoCultivo: 'permanente', cultivo: miCultivo.value.permanente }
      : { tipoCultivo: 'temporal', mesSiembra: mesSiembra.value },
  )

  // --- Última recomendación (también cache offline) ---
  const recomendacion = ref<Recomendacion | null>(leer<Recomendacion>(CLAVES.recomendacion))
  const estado = ref<EstadoCarga>('inicial')
  const error = ref<ApiError | null>(null)
  /** true cuando se muestra la recomendación guardada porque falló la red */
  const desdeCache = ref(false)
  const cargando = computed(() => estado.value === 'cargando')

  /** true si la recomendación guardada corresponde a la parcela actual */
  const recomendacionEsDeParcela = computed(() => {
    const r = recomendacion.value
    const p = parcela.value
    return !!r && !!p && Math.abs(r.lat - p.lat) < 0.01 && Math.abs(r.lon - p.lon) < 0.01
  })

  async function cargarRecomendacion() {
    if (!parcela.value) return
    estado.value = 'cargando'
    error.value = null
    const origen = useOrigenStore()
    const t = i18n.global.t
    const { lat, lon } = parcela.value
    try {
      const r = await api.getRecomendacion(lat, lon, idioma.value, opcionesCultivo.value)
      recomendacion.value = r
      // Solo se guarda como copia offline un dato real (nunca un ejemplo)
      if (MODO !== 'ejemplo') guardar(CLAVES.recomendacion, r)
      desdeCache.value = false
      estado.value = 'listo'
    } catch (e) {
      error.value = e instanceof ApiError ? e : new ApiError(String(e), 'desconocido')
      const guardada = leer<Recomendacion>(CLAVES.recomendacion)
      if (guardada) {
        // 1) Copia guardada, con su fecha y aviso
        recomendacion.value = guardada
        desdeCache.value = true
        estado.value = 'listo'
        origen.registrar('recomendacion', 'cache')
        origen.avisar(t('origen.usandoCache', { fecha: guardada.fecha }))
      } else if (MODO === 'python') {
        // 2) Sin copia: datos de ejemplo, con banner y aviso
        recomendacion.value = await api.getRecomendacionEjemplo(lat, lon, idioma.value, opcionesCultivo.value)
        desdeCache.value = false
        estado.value = 'listo'
        origen.registrar('recomendacion', 'ejemplo')
        origen.avisar(t('origen.servicioCaido'))
      } else {
        estado.value = 'error'
      }
    }
  }

  // Al cambiar de cultivo o de mes de siembra, pedir de nuevo los datos
  watch(
    () => JSON.stringify(opcionesCultivo.value),
    () => {
      if (parcela.value) cargarRecomendacion()
    },
  )

  /** Indicadores en nivel alto, para el banner de alerta */
  const indicadoresAltos = computed<ClaveIndicador[]>(() => {
    const ind = recomendacion.value?.indicadores
    if (!ind) return []
    return (Object.keys(ind) as ClaveIndicador[]).filter((k) => ind[k]?.nivel === 'alto')
  })

  /** Riesgo general = el peor nivel entre los indicadores */
  const nivelGeneral = computed<NivelRiesgo>(() => {
    const ind = recomendacion.value?.indicadores
    if (!ind) return 'bajo'
    const niveles = Object.values(ind).map((i) => i?.nivel)
    return niveles.includes('alto') ? 'alto' : niveles.includes('medio') ? 'medio' : 'bajo'
  })

  /** Rotación con mayor puntaje */
  const mejorRotacion = computed(() => {
    const rot = recomendacion.value?.rotaciones ?? []
    return rot.length ? rot.reduce((a, b) => (b.puntaje > a.puntaje ? b : a)) : null
  })

  return {
    parcela,
    elegirParcela,
    ubicando,
    pedirUbicacion,
    miCultivo,
    tipoCultivo,
    mesSiembra,
    opcionesCultivo,
    cargando,
    recomendacionEsDeParcela,
    nivelGeneral,
    idioma,
    tema,
    alternarTema,
    onboardingVisto,
    completarOnboarding,
    recomendacion,
    estado,
    error,
    desdeCache,
    cargarRecomendacion,
    indicadoresAltos,
    mejorRotacion,
  }
})
