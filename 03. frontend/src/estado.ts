// Estado global simple (sin librerías): parcela, idioma, tema, ruta y resultado.
import { reactive, watch } from 'vue'
import { zonas, type Piso } from './data/catalogo'
import { leerNasa, type DatosNasa } from './motor/nasa'
import { accionRecomendada, calcularIndicadores, evaluarRotaciones, type Accion, type Indicadores, type Rotacion } from './motor/riesgo'

export type Ruta = 'campana' | 'siembro' | 'mapa' | 'funciona' | 'ayuda'

function leer<T>(k: string, def: T): T {
  try { const v = localStorage.getItem('allpashift.' + k); return v ? (JSON.parse(v) as T) : def } catch { return def }
}
function guardar(k: string, v: unknown) {
  try { localStorage.setItem('allpashift.' + k, JSON.stringify(v)) } catch { /* sin almacenamiento */ }
}

export interface Parcela { nombre: string; lat: number; lon: number }

const hoy = new Date()
export const estado = reactive({
  ruta: ((location.hash.replace('#/', '') || 'mapa') as Ruta),
  idioma: leer<'es' | 'en'>('idioma', 'es'),
  tema: leer<'claro' | 'oscuro'>('tema', 'claro'),
  parcela: leer<Parcela>('parcela', { nombre: 'Medio Piura - Castilla, Perú', lat: -5.2, lon: -80.62 }),
  modo: 'sembrar' as 'sembrar' | 'permanente',
  permanente: 'Mango',
  mesSiembra: hoy.getMonth(),        // 0..11
  cargando: false,
  datos: null as DatosNasa | null,
  ind: null as Indicadores | null,
  rotaciones: [] as Rotacion[],
  accion: null as Accion | null,
  asistenteAbierto: false,
})

export const fechaHoy = hoy

export function irA(r: Ruta) { location.hash = '#/' + r }
window.addEventListener('hashchange', () => { estado.ruta = (location.hash.replace('#/', '') || 'mapa') as Ruta })

watch(() => estado.idioma, (v) => guardar('idioma', v))
watch(() => estado.tema, (v) => { guardar('tema', v); document.documentElement.dataset.theme = v === 'oscuro' ? 'dark' : 'light' }, { immediate: true })
watch(() => estado.parcela, (v) => guardar('parcela', v), { deep: true })

export function pisoDe(lat: number, lon: number): Piso {
  let mejor = zonas[0], dist = Infinity
  for (const z of zonas) { const dd = (z.lat - lat) ** 2 + (z.lon - lon) ** 2; if (dd < dist) { dist = dd; mejor = z } }
  return dist < 0.5 ? mejor.piso : 'costa'
}

export function valleCercano(lat: number, lon: number) {
  let mejor = null as null | (typeof zonas)[number], dist = Infinity
  for (const z of zonas) { const dd = (z.lat - lat) ** 2 + (z.lon - lon) ** 2; if (dd < dist) { dist = dd; mejor = z } }
  return dist < 0.3 ? mejor : null
}

export async function analizar() {
  estado.cargando = true
  try {
    const d = await leerNasa(estado.parcela.lat, estado.parcela.lon)
    estado.datos = d
    recalcular()
  } finally {
    estado.cargando = false
  }
}

export function recalcular() {
  if (!estado.datos) return
  const ind = calcularIndicadores(estado.datos, hoy.getMonth())
  const anio = hoy.getFullYear() + (estado.mesSiembra < hoy.getMonth() ? 1 : 0)
  estado.ind = ind
  estado.rotaciones = evaluarRotaciones(estado.datos, ind, pisoDe(estado.parcela.lat, estado.parcela.lon), estado.mesSiembra, anio)
  estado.accion = accionRecomendada(ind, estado.mesSiembra, estado.rotaciones[0])
}

watch(() => estado.mesSiembra, recalcular)
