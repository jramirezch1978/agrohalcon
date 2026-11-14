// Contratos de la API del backend Java. Mantener sincronizado con el backend.

export type NivelRiesgo = 'bajo' | 'medio' | 'alto'

/** Fuentes reales que usa AgroShift. 'Ejemplo' = dato simulado (modo demo sin servicio de cálculos). */
export type FuenteNasa = 'NASA POWER' | 'GPM IMERG' | 'MUR SST' | 'Ejemplo'

export type ClaveIndicador = 'lluvia' | 'humedadSuelo' | 'calor' | 'elNino'

/** Fuente de un dato: una misión o una combinación (ej. "NASA POWER + MUR SST") */
export type FuenteDato = FuenteNasa | (string & {})

/** Temporal = se rota (arroz, maíz…). Permanente = dura años (mango, limón, banano) */
export type TipoCultivo = 'temporal' | 'permanente'
export type CultivoPermanente = 'mango' | 'limon' | 'banano'

/** Tipo de acción de la quincena */
export type TipoAccion = 'sembrar' | 'esperar' | 'regar' | 'proteger' | 'preparar drenaje'

/** Mes en formato "AAAA-MM", ej. "2026-12" */
export type MesISO = string

export interface Indicador {
  valor: number
  normal: number
  unidad: string
  nivel: NivelRiesgo
  fuente: FuenteNasa
  /** Opcional: texto en palabras simples con el número que decide ("Lluvia 45 % bajo lo normal…") */
  detalle?: string
  /** Opcional: aviso de calidad del dato (p. ej. dato satelital atrasado) */
  aviso?: string
}

/** Un indicador puede faltar si no hay dato real (p. ej. El Niño sin MUR SST): nunca se rellena. */
export type Indicadores = Partial<Record<ClaveIndicador, Indicador>>

/** Puntos que un indicador (o el riesgo de la campaña) le restó o sumó a una rotación */
export interface Descuento {
  /** 'campana' = efecto del mes de siembra sobre el riesgo de toda la campaña */
  indicador: ClaveIndicador | 'campana'
  puntos: number // negativo, ej. -40
  fuente: FuenteDato
}

export interface Rotacion {
  id: number
  nombre: string
  puntaje: number // 0 - 100
  riesgo: NivelRiesgo
  explicacion: string
  /** Opcional: uso de agua estimado */
  usoAgua?: NivelRiesgo
  /** Opcional: qué indicadores le restaron puntos */
  descuentos?: Descuento[]
  /** Opcional: riesgo de la campaña mes a mes, de la siembra a la cosecha */
  ciclo?: CicloCultivo
}

/** Riesgo de un mes de la campaña (clima histórico NASA POWER + señal de El Niño) */
export interface MesRiesgo {
  mes: MesISO
  riesgo: NivelRiesgo
  motivo: string
  fuente: FuenteDato
}

export interface CicloCultivo {
  siembra: MesISO
  cosecha: MesISO
  duracionMeses: number
  meses: MesRiesgo[]
  mesMasRiesgoso?: MesISO
}

/** Mes del plan de un cultivo permanente: etapa + riesgo */
export interface MesEtapa extends MesRiesgo {
  etapa: string // "floración", "fructificación", "cosecha"…
}

export interface AccionEtapa {
  etapa: string
  accion: string
  motivo: string
  fuente: FuenteDato
}

/** Plan anual de un cultivo permanente (GET /api/recomendacion?tipoCultivo=permanente&cultivo=) */
export interface PlanPermanente {
  cultivo: string
  etapaActual: string
  meses: MesEtapa[]
  acciones: AccionEtapa[]
}

export interface QueHacer {
  /** Opcional: tipo de acción (muestra un ícono en la tarjeta principal) */
  tipo?: TipoAccion
  accion: string
  motivo: string
  fuente: FuenteDato
}

/** GET /api/recomendacion?lat=&lon=&tipoCultivo=&mesSiembra=&cultivo= */
export interface Recomendacion {
  lat: number
  lon: number
  fecha: string // ISO yyyy-mm-dd
  indicadores: Indicadores
  rotaciones: Rotacion[]
  queHacer: QueHacer
  /** Opcional: solo para cultivos permanentes */
  plan?: PlanPermanente
}

/** Parámetros opcionales de /api/recomendacion */
export interface OpcionesRecomendacion {
  tipoCultivo?: TipoCultivo
  /** Solo temporal: mes de siembra "AAAA-MM" */
  mesSiembra?: MesISO
  /** Solo permanente */
  cultivo?: CultivoPermanente
}

export interface ZonaRiesgo {
  nombre: string
  lat: number
  lon: number
  /** null = sin dato real (modo ejemplo): se dibuja en gris */
  nivel: NivelRiesgo | null
}

/** GET /api/mapa?region= */
export interface MapaRiesgo {
  region: string
  zonas: ZonaRiesgo[]
}

/** GET /api/cultivos */
export interface Cultivo {
  id: number
  nombre: string
  usoAgua: NivelRiesgo
  toleranciaCalor: NivelRiesgo
  toleranciaSequia: NivelRiesgo
  cicloDias: number
}

/** Serie mensual de /validacion (null = sin dato; nunca se rellena) */
export interface SerieValidacion {
  unidad: string
  fuente: FuenteDato | 'sin dato'
  valores: (number | null)[]
  normal: (number | null)[]
  producto?: string
}

export interface AlertaValidacion {
  /** Fecha (AAAA-MM-DD) en que se habría disparado la alerta con las reglas de hoy */
  fecha: string
  accion: string
  motivo: string
  indicador: 'elNino' | 'lluvia'
  nivel: NivelRiesgo
  valor: number
  fuente: FuenteDato
  /** Primera semana en nivel alto (regla de "preparar drenaje") */
  alertaDrenaje?: { fecha: string; valor: number; fuente: FuenteDato } | null
  /** Solo si la alerta se calculó sin MUR SST */
  nota?: string
}

/** GET /validacion?anio=&lat=&lon=&lang= (servicio de cálculos) */
export interface Validacion {
  anio: number
  lat: number
  lon: number
  evento: { nombre: string; inicio: MesISO; fin: MesISO } | null
  series: { lluvia: SerieValidacion; humedadSuelo?: SerieValidacion; ndvi?: SerieValidacion }
  alerta: AlertaValidacion | null
  mesLluviaMaxima: MesISO | null
  semanasAnticipacion: number | null
  realidad: { resumen: string; fuente: string } | null
  recomendacionPrevia: QueHacer
  resumen: string
}

/** GET /validacion/anios: años con datos reales */
export interface AniosValidacion {
  anios: number[]
  fuente: FuenteDato
  conMurSst: number[]
}

/** POST /api/asistente (cuerpo) */
export interface PreguntaAsistente {
  lat: number
  lon: number
  pregunta: string
  idioma: 'es' | 'en'
  tipoCultivo?: TipoCultivo
  mesSiembra?: MesISO
  cultivo?: CultivoPermanente
}

/** Respuesta del asistente: plantillas sobre resultados ya calculados (sin IA). */
export interface RespuestaAsistente {
  respuesta: string
  /** Solo las fuentes que trae la recomendación calculada */
  fuentes: FuenteDato[]
}
