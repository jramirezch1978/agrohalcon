import { CloudRain, Thermometer, Waves } from 'lucide-vue-next'
import type { FuenteNasa } from '@/types/api'

/**
 * Fuentes de la NASA que AgroShift usa DE VERDAD (servicio de cálculos en Python).
 * Para editar: nombres, misiones y enlaces van aquí; los textos "qué mide" y "para qué sirve"
 * van en i18n (datos.items.<id>) en ES y EN.
 */
export interface NasaDataset {
  id: 'power' | 'imerg' | 'sst'
  nombre: FuenteNasa
  mision: string
  resolucion: string
  url: string
  icono: typeof CloudRain
  /** Degradado de la cabecera de la tarjeta (clases Tailwind) */
  color: string
}

export const NASA_DATASETS: NasaDataset[] = [
  {
    id: 'power',
    nombre: 'NASA POWER',
    mision: 'Prediction Of Worldwide Energy Resources (NASA LaRC), API v2.10, comunidad AG',
    resolucion: '~0.5° · diario y climatología 2001-2025',
    url: 'https://power.larc.nasa.gov/',
    icono: Thermometer,
    color: 'from-amber-600 to-orange-800',
  },
  {
    id: 'imerg',
    nombre: 'GPM IMERG',
    mision: 'Global Precipitation Measurement (NASA / JAXA), IMERG V07 Final y Late, NASA GES DISC',
    resolucion: '0.1° (~10 km) · diario y mensual',
    url: 'https://gpm.nasa.gov/data/imerg',
    icono: CloudRain,
    color: 'from-nasa-500 to-nasa-900',
  },
  {
    id: 'sst',
    nombre: 'MUR SST',
    mision: 'MUR SST v4.1 (NASA JPL PO.DAAC), vía ERDDAP de NOAA CoastWatch',
    resolucion: '0.01° (usamos 0.25°) · semanal, caja Niño 1+2',
    url: 'https://podaac.jpl.nasa.gov/dataset/MUR-JPL-L4-GLOB-v4.1',
    icono: Waves,
    color: 'from-cyan-600 to-teal-900',
  },
]
