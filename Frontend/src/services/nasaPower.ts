/**
 * Clima histórico REAL de NASA POWER (API pública, sin clave) para cualquier punto del mundo.
 * https://power.larc.nasa.gov/docs/services/api/temporal/climatology/
 *
 * Se usa en modo demo (USE_MOCK=true) para que los valores "normales" y la estacionalidad
 * de la campaña sean reales. Con el backend Java, este cálculo lo hace el backend.
 */

export interface ClimaPower {
  /** Lluvia promedio por mes (mm/día), enero..diciembre — PRECTOTCORR */
  lluvia: number[]
  /** Temperatura media por mes (°C), enero..diciembre — T2M */
  temperatura: number[]
  /** true si vino de la API; false si es el respaldo guardado en el código */
  real: boolean
}

const MESES = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

/**
 * Respaldo sin internet: climatología de NASA POWER para Piura (-5.19, -80.63),
 * descargada de la misma API el 14/11/2026.
 */
export const CLIMA_PIURA: ClimaPower = {
  lluvia: [0.39, 1.24, 1.69, 0.42, 0.13, 0.07, 0.07, 0.04, 0.04, 0.13, 0.15, 0.24],
  temperatura: [27.09, 27.83, 28.0, 27.4, 25.95, 24.43, 23.56, 23.41, 23.74, 24.06, 24.56, 25.86],
  real: false,
}

const cache = new Map<string, Promise<ClimaPower | null>>()
const clave = (lat: number, lon: number) => `${(Math.round(lat * 2) / 2).toFixed(1)},${(Math.round(lon * 2) / 2).toFixed(1)}` // celda de 0.5°

function leerGuardado(k: string): ClimaPower | null {
  try {
    const raw = localStorage.getItem(`agroshift:power:${k}`)
    return raw ? (JSON.parse(raw) as ClimaPower) : null
  } catch {
    return null
  }
}

async function descargar(lat: number, lon: number, k: string): Promise<ClimaPower | null> {
  const guardado = leerGuardado(k)
  if (guardado) return guardado

  const url = new URL('https://power.larc.nasa.gov/api/temporal/climatology/point')
  url.search = new URLSearchParams({
    parameters: 'PRECTOTCORR,T2M',
    community: 'AG',
    latitude: lat.toFixed(3),
    longitude: lon.toFixed(3),
    format: 'JSON',
  }).toString()

  const control = new AbortController()
  const t = setTimeout(() => control.abort(), 8000)
  try {
    const res = await fetch(url, { signal: control.signal })
    if (!res.ok) return null
    const json = (await res.json()) as { properties?: { parameter?: Record<string, Record<string, number>> } }
    const p = json.properties?.parameter
    if (!p?.PRECTOTCORR || !p?.T2M) return null
    const valido = (v: number) => Number.isFinite(v) && v > -900 // -999 = sin dato
    const lluvia = MESES.map((m) => p.PRECTOTCORR[m])
    const temperatura = MESES.map((m) => p.T2M[m])
    if (!lluvia.every(valido) || !temperatura.every(valido)) return null
    const clima: ClimaPower = { lluvia, temperatura, real: true }
    try {
      localStorage.setItem(`agroshift:power:${k}`, JSON.stringify(clima))
    } catch {
      /* sin almacenamiento */
    }
    return clima
  } catch {
    return null // sin internet o tiempo agotado
  } finally {
    clearTimeout(t)
  }
}

/** Climatología mensual de NASA POWER (con caché por celda de 0.5°). Nunca lanza error: devuelve null. */
export function climatologiaPower(lat: number, lon: number): Promise<ClimaPower | null> {
  const k = clave(lat, lon)
  if (!cache.has(k)) {
    // Si falla, no se guarda en caché: se reintenta la próxima vez
    cache.set(k, descargar(lat, lon, k).then((r) => (r ? r : (cache.delete(k), null))))
  }
  return cache.get(k)!
}
