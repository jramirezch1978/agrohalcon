// Lectura de datos NASA desde el navegador (APIs públicas con CORS).
// NASA POWER: climatología (normal) y diario reciente. MUR SST (ERDDAP): temperatura del mar.

const POWER = 'https://power.larc.nasa.gov/api/temporal'
const PARAMS = 'PRECTOTCORR,GWETTOP,GWETROOT,T2M_MAX,T2M'
const MESES_API = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

export interface Normal { lluviaMmDia: number; humedadSup: number; humedadRaiz: number; tMax: number; tMed: number }
export interface Reciente { lluviaMm30: number; humedadSup: number; tMax: number; ultimoDia: string }
export interface DatosNasa {
  normales: Normal[]            // 12 meses (normal climatológica de NASA POWER)
  reciente: Reciente | null     // últimos 30 días con dato
  sstAnomalia: number | null    // °C frente a lo normal, frente a la costa (MUR SST)
  fuente: 'NASA POWER' | 'Ejemplo'
}

const cache = new Map<string, DatosNasa>()

function fmt(d: Date) {
  return d.toISOString().slice(0, 10).replace(/-/g, '')
}

async function json(url: string, ms = 20000) {
  const ctl = new AbortController()
  const t = setTimeout(() => ctl.abort(), ms)
  try {
    const r = await fetch(url, { signal: ctl.signal })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return await r.json()
  } finally {
    clearTimeout(t)
  }
}

export async function leerNasa(lat: number, lon: number): Promise<DatosNasa> {
  const clave = `${lat.toFixed(2)},${lon.toFixed(2)}`
  const enCache = cache.get(clave)
  if (enCache) return enCache
  try {
    const hoy = new Date()
    const ini = new Date(hoy.getTime() - 45 * 86400000)
    const [clim, diario, sst] = await Promise.all([
      json(`${POWER}/climatology/point?parameters=${PARAMS}&community=AG&longitude=${lon}&latitude=${lat}&format=JSON`),
      json(`${POWER}/daily/point?parameters=PRECTOTCORR,GWETTOP,T2M_MAX&community=AG&longitude=${lon}&latitude=${lat}&start=${fmt(ini)}&end=${fmt(hoy)}&format=JSON`).catch(() => null),
      leerSst(lat, lon).catch(() => null),
    ])
    const p = clim.properties.parameter
    const normales: Normal[] = MESES_API.map((m) => ({
      lluviaMmDia: p.PRECTOTCORR[m], humedadSup: p.GWETTOP[m], humedadRaiz: p.GWETROOT[m], tMax: p.T2M_MAX[m], tMed: p.T2M[m],
    }))
    let reciente: Reciente | null = null
    if (diario) {
      const d = diario.properties.parameter
      const dias = Object.keys(d.T2M_MAX).filter((k) => d.T2M_MAX[k] !== -999 && d.GWETTOP[k] !== -999 && d.PRECTOTCORR[k] !== -999).slice(-30)
      if (dias.length >= 10) {
        const prom = (o: Record<string, number>) => dias.reduce((s, k) => s + o[k], 0) / dias.length
        reciente = {
          lluviaMm30: dias.reduce((s, k) => s + d.PRECTOTCORR[k], 0) * (30 / dias.length),
          humedadSup: prom(d.GWETTOP),
          tMax: prom(d.T2M_MAX),
          ultimoDia: dias[dias.length - 1],
        }
      }
    }
    const datos: DatosNasa = { normales, reciente, sstAnomalia: sst, fuente: 'NASA POWER' }
    cache.set(clave, datos)
    return datos
  } catch {
    return ejemplo()
  }
}

// Anomalía de temperatura del mar frente a la costa más cercana (solo tiene sentido en la costa del Pacífico)
async function leerSst(lat: number, lon: number): Promise<number | null> {
  if (lon > -78 || lat < -20 || lat > 5) return null
  const la = Math.max(-18, Math.min(2, lat)).toFixed(2)
  const lo = Math.min(lon - 0.9, -81.2).toFixed(2)
  const r = await fetch(`/nasa/erddap/griddap/jplMURSST41anom1day.json?sstAnom%5B(last)%5D%5B(${la})%5D%5B(${lo})%5D`)
  if (!r.ok) return null
  const j = await r.json()
  const v = j.table.rows[0][3]
  return typeof v === 'number' ? v : null
}

// Datos de ejemplo (si NASA no responde): costa norte seca, suelo 38 % por debajo de lo normal
export function ejemplo(): DatosNasa {
  const lluvia = [0.4, 1.2, 1.7, 0.4, 0.1, 0.1, 0.1, 0.04, 0.04, 0.1, 0.15, 0.25]
  const normales = lluvia.map((l, i) => ({ lluviaMmDia: l, humedadSup: 0.24, humedadRaiz: 0.4, tMax: 34 + (i < 4 ? 3 : 0), tMed: 25 }))
  return { normales, reciente: { lluviaMm30: 0.5, humedadSup: 0.24 * 0.62, tMax: 35, ultimoDia: '' }, sstAnomalia: null, fuente: 'Ejemplo' }
}

// Serie mensual de un año (para la máquina del tiempo)
export async function serieMensual(lat: number, lon: number, anio1: number, anio2: number) {
  const j = await json(`${POWER}/monthly/point?parameters=PRECTOTCORR,GWETROOT&community=AG&longitude=${lon}&latitude=${lat}&start=${anio1}&end=${anio2}&format=JSON`)
  const p = j.properties.parameter
  const claves = Object.keys(p.PRECTOTCORR).filter((k) => !k.endsWith('13'))
  return claves.map((k) => ({ mes: k, lluviaMmDia: p.PRECTOTCORR[k] as number, humedadRaiz: p.GWETROOT[k] as number }))
}
