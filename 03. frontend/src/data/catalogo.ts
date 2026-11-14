// Catálogo de AllpaShift (PRELIMINAR: se valida con MIDAGRI / FAO-56).
// Es un subconjunto de la base de datos (agro.cultivos, agro.zonas, agro.rotaciones; doc 26).

export type Fase = 'S' | 'C' | 'F' | 'K' | 'D'
export type Piso = 'costa' | 'sierra' | 'selva'
export type Agua = 'baja' | 'media' | 'alta'

export interface Zona { id: number; nombre: string; lat: number; lon: number; region: string; piso: Piso }

// 18 valles (mismos que agro.zonas)
export const zonas: Zona[] = [
  { id: 1, nombre: 'Bajo Piura', lat: -5.35, lon: -80.7, region: 'Piura', piso: 'costa' },
  { id: 2, nombre: 'Valle del Chira', lat: -4.9, lon: -80.85, region: 'Piura', piso: 'costa' },
  { id: 3, nombre: 'Medio Piura - Castilla', lat: -5.2, lon: -80.62, region: 'Piura', piso: 'costa' },
  { id: 4, nombre: 'San Lorenzo - Tambogrande', lat: -4.93, lon: -80.34, region: 'Piura', piso: 'costa' },
  { id: 5, nombre: 'Alto Piura - Chulucanas', lat: -5.1, lon: -80.16, region: 'Piura', piso: 'costa' },
  { id: 6, nombre: 'Sechura - Bernal / Vice', lat: -5.45, lon: -80.8, region: 'Piura', piso: 'costa' },
  { id: 7, nombre: 'Sierra - Huancabamba', lat: -5.24, lon: -79.45, region: 'Piura', piso: 'sierra' },
  { id: 17, nombre: 'Sierra - Huarmaca', lat: -5.57, lon: -79.52, region: 'Piura', piso: 'sierra' },
  { id: 18, nombre: 'Sierra - Ayabaca', lat: -4.64, lon: -79.71, region: 'Piura', piso: 'sierra' },
  { id: 8, nombre: 'Valle de Tumbes', lat: -3.57, lon: -80.45, region: 'Tumbes', piso: 'costa' },
  { id: 9, nombre: 'Chancay-Lambayeque', lat: -6.7, lon: -79.9, region: 'Lambayeque', piso: 'costa' },
  { id: 10, nombre: 'Olmos', lat: -5.99, lon: -79.74, region: 'Lambayeque', piso: 'costa' },
  { id: 11, nombre: 'Jequetepeque', lat: -7.2, lon: -79.45, region: 'La Libertad', piso: 'costa' },
  { id: 12, nombre: 'Chavimochic - Virú', lat: -8.41, lon: -78.75, region: 'La Libertad', piso: 'costa' },
  { id: 13, nombre: 'Jaén', lat: -5.71, lon: -78.81, region: 'Cajamarca', piso: 'selva' },
  { id: 14, nombre: 'Valle de Cajamarca', lat: -7.16, lon: -78.5, region: 'Cajamarca', piso: 'sierra' },
  { id: 15, nombre: 'Bagua - Utcubamba', lat: -5.64, lon: -78.53, region: 'Amazonas', piso: 'selva' },
  { id: 16, nombre: 'Alto Mayo - Moyobamba', lat: -6.03, lon: -76.97, region: 'San Martín', piso: 'selva' },
]

export interface Cultivo {
  nombre: string
  nombreEn: string
  agua: Agua
  cicloMeses: number          // anual: meses de siembra a cosecha
  toleraSequia: boolean
  toleraCalor: boolean
  toleraInundacion: boolean
  fijaNitrogeno: boolean
  tempMax: number             // °C por encima de la cual sufre
  permanente?: boolean
  calendario?: string         // 12 letras ene..dic (permanentes)
}

export const cultivos: Record<string, Cultivo> = {
  'Frijol caupí': { nombre: 'Frijol caupí', nombreEn: 'Cowpea', agua: 'baja', cicloMeses: 3, toleraSequia: true, toleraCalor: true, toleraInundacion: false, fijaNitrogeno: true, tempMax: 35 },
  Frijol: { nombre: 'Frijol', nombreEn: 'Bean', agua: 'baja', cicloMeses: 3, toleraSequia: true, toleraCalor: true, toleraInundacion: false, fijaNitrogeno: true, tempMax: 33 },
  Zarandaja: { nombre: 'Zarandaja', nombreEn: 'Lablab bean', agua: 'baja', cicloMeses: 4, toleraSequia: true, toleraCalor: true, toleraInundacion: false, fijaNitrogeno: true, tempMax: 35 },
  Maíz: { nombre: 'Maíz', nombreEn: 'Maize', agua: 'media', cicloMeses: 5, toleraSequia: false, toleraCalor: true, toleraInundacion: false, fijaNitrogeno: false, tempMax: 34 },
  Algodón: { nombre: 'Algodón', nombreEn: 'Cotton', agua: 'media', cicloMeses: 7, toleraSequia: true, toleraCalor: false, toleraInundacion: false, fijaNitrogeno: false, tempMax: 35 },
  Arroz: { nombre: 'Arroz', nombreEn: 'Rice', agua: 'alta', cicloMeses: 4, toleraSequia: false, toleraCalor: true, toleraInundacion: true, fijaNitrogeno: false, tempMax: 36 },
  Sandía: { nombre: 'Sandía', nombreEn: 'Watermelon', agua: 'media', cicloMeses: 3, toleraSequia: false, toleraCalor: true, toleraInundacion: false, fijaNitrogeno: false, tempMax: 35 },
  Camote: { nombre: 'Camote', nombreEn: 'Sweet potato', agua: 'baja', cicloMeses: 4, toleraSequia: true, toleraCalor: true, toleraInundacion: false, fijaNitrogeno: false, tempMax: 34 },
  Papa: { nombre: 'Papa', nombreEn: 'Potato', agua: 'media', cicloMeses: 5, toleraSequia: false, toleraCalor: false, toleraInundacion: false, fijaNitrogeno: false, tempMax: 26 },
  Arveja: { nombre: 'Arveja', nombreEn: 'Pea', agua: 'media', cicloMeses: 4, toleraSequia: false, toleraCalor: false, toleraInundacion: false, fijaNitrogeno: true, tempMax: 25 },
  Trigo: { nombre: 'Trigo', nombreEn: 'Wheat', agua: 'media', cicloMeses: 5, toleraSequia: true, toleraCalor: false, toleraInundacion: false, fijaNitrogeno: false, tempMax: 27 },
  'Maíz amiláceo': { nombre: 'Maíz amiláceo', nombreEn: 'Andean maize', agua: 'media', cicloMeses: 6, toleraSequia: false, toleraCalor: false, toleraInundacion: false, fijaNitrogeno: false, tempMax: 28 },
  // Permanentes: reciben acciones, no rotaciones
  Mango: { nombre: 'Mango', nombreEn: 'Mango', agua: 'media', cicloMeses: 12, toleraSequia: true, toleraCalor: true, toleraInundacion: false, fijaNitrogeno: false, tempMax: 38, permanente: true, calendario: 'KKKDDCFFFCKK' },
  Limón: { nombre: 'Limón', nombreEn: 'Lime', agua: 'media', cicloMeses: 12, toleraSequia: false, toleraCalor: true, toleraInundacion: false, fijaNitrogeno: false, tempMax: 36, permanente: true, calendario: 'KKKKKCCFFCCK' },
  'Uva de mesa': { nombre: 'Uva de mesa', nombreEn: 'Table grape', agua: 'media', cicloMeses: 12, toleraSequia: true, toleraCalor: false, toleraInundacion: false, fijaNitrogeno: false, tempMax: 35, permanente: true, calendario: 'KDDDDDCFCKKK' },
  'Banano orgánico': { nombre: 'Banano orgánico', nombreEn: 'Organic banana', agua: 'alta', cicloMeses: 12, toleraSequia: false, toleraCalor: true, toleraInundacion: false, fijaNitrogeno: false, tempMax: 36, permanente: true, calendario: 'KKKKKKKKKKKK' },
  Palta: { nombre: 'Palta', nombreEn: 'Avocado', agua: 'alta', cicloMeses: 12, toleraSequia: false, toleraCalor: false, toleraInundacion: false, fijaNitrogeno: false, tempMax: 32, permanente: true, calendario: 'CCKKKKCFFCCC' },
  Cacao: { nombre: 'Cacao', nombreEn: 'Cocoa', agua: 'alta', cicloMeses: 12, toleraSequia: false, toleraCalor: true, toleraInundacion: false, fijaNitrogeno: false, tempMax: 34, permanente: true, calendario: 'CCKKKKCCCFFC' },
  Café: { nombre: 'Café', nombreEn: 'Coffee', agua: 'alta', cicloMeses: 12, toleraSequia: false, toleraCalor: false, toleraInundacion: false, fijaNitrogeno: false, tempMax: 30, permanente: true, calendario: 'CCFKKKKKCFCC' },
}

export const permanentes = Object.values(cultivos).filter((c) => c.permanente).map((c) => c.nombre)

// Rotaciones a comparar por piso (la última es la práctica actual)
export const rotacionesPorPiso: Record<Piso, [string, string][]> = {
  costa: [['Frijol caupí', 'Maíz'], ['Maíz', 'Algodón'], ['Arroz', 'Arroz']],
  sierra: [['Papa', 'Arveja'], ['Maíz amiláceo', 'Trigo'], ['Papa', 'Papa']],
  selva: [['Frijol', 'Maíz'], ['Maíz', 'Arroz'], ['Arroz', 'Arroz']],
}

export const nombreFase: Record<Fase, string> = { S: 'Siembra', C: 'Crecimiento', F: 'Floración', K: 'Cosecha', D: 'Descanso / poda' }

export const accionPermanente: Record<string, Partial<Record<Fase, string>>> = {
  Mango: { F: 'Riego controlado para inducir floración; vigila oídio y trips.', K: 'Planifica cosecha y acopio antes de las lluvias de verano.', C: 'Fertiliza y riega según la humedad del suelo.', D: 'Poda de formación y limpieza tras la cosecha.' },
  Limón: { F: 'Asegura riego y nutrición para una buena floración.', K: 'Drena la parcela y controla hongos si llueve.', C: 'Riega según el balance hídrico y vigila plagas.' },
  'Uva de mesa': { D: 'Poda de producción y aplicación para uniformizar la brotación.', C: 'Raleo de racimos y riego de crecimiento.', F: 'Evita estrés hídrico durante la floración y el cuajado.', K: 'Protege racimos y adelanta cosecha si se anuncian lluvias.' },
  'Banano orgánico': { K: 'Cosecha continua; vigila la marchitez por Fusarium.', C: 'Riego frecuente y deshije.' },
  Palta: { F: 'Riego sin encharcar durante la floración.', K: 'Cosecha por madurez fisiológica.', C: 'Riego y nutrición; cuida el calor extremo.' },
  Cacao: { K: 'Cosecha de mazorcas maduras y fermentación.', F: 'Mantén sombra y humedad.', C: 'Poda sanitaria y control de monilia.' },
  Café: { K: 'Cosecha selectiva de granos maduros.', F: 'Protege la floración del estrés hídrico.', C: 'Fertiliza y maneja la sombra.' },
}

export const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
export const MESES_EN = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
export const MES_CORTO = ['E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
