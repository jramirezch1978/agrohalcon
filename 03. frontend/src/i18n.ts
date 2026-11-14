import { estado } from './estado'

const T = {
  es: {
    sub: 'Con datos satelitales de la NASA',
    queHago: '¿Qué hago?', queSiembro: '¿Qué siembro?', mapa: 'Mapa', funciona: '¿Funciona?', ayuda: 'Ayuda',
    buscar: 'Buscar un lugar del mundo…', miUbicacion: 'Usar mi ubicación', nivelRiesgo: 'Nivel de riesgo',
    alto: 'Alto', medio: 'Medio', bajo: 'Bajo', miParcela: 'Mi parcela', coordenadas: 'Coordenadas', analizar: 'Analizar esta parcela',
    queHagoAhora: '¿Qué hago ahora?', accion2sem: 'La acción para las próximas 2 semanas. El riesgo de toda la campaña lo ves en «¿Qué siembro?»',
    enQue: '¿En qué te ayudamos?', recomiendame: 'Recomiéndame qué sembrar', recomiendameSub: 'Te decimos qué cultivo de temporada conviene en tu parcela',
    tengoPermanente: 'Ya tengo un cultivo permanente', tengoPermanenteSub: 'Mango, limón, banano, etc.',
    cambiarParcela: 'Cambiar parcela', alerta: 'Alerta', accionRec: 'Acción recomendada', riesgoClim: 'Riesgo climático', motivo: 'Motivo',
    dato: 'Dato', siembraPlaneada: 'Siembra planeada', cambiar: 'Cambiar', whatsapp: 'Compartir por WhatsApp', mejorRot: 'Mejor rotación',
    pregunta: 'Pregúntale a AllpaShift', preguntaSub: 'Resuelve tus dudas sobre esta recomendación',
    satelites: 'Lo que ven los satélites', satelitesSub: 'Toca un indicador para ver por qué',
    queConviene: '¿Qué me conviene sembrar?', tocaTarjeta: 'Toca una tarjeta para ver por qué tiene ese puntaje', cuando: '¿Cuándo vas a sembrar?',
    esteMes: 'Este mes', proximo: 'El próximo', en2: 'En 2 meses',
    aviso: 'AllpaShift no predice el clima exacto a meses. Estima el riesgo de la campaña combinando el historial climático de la NASA con señales tempranas como El Niño.',
    recomendada: 'Recomendada', usoAgua: 'Uso de agua', porQue: '¿Por qué este puntaje?', perspectiva: 'Perspectiva de la campaña',
    siembra: 'Siembra', cosecha: 'Cosecha', duracion: 'Duración', meses: 'meses', masRiesgoso: 'Mes más riesgoso', tocaMes: 'Toca un mes para ver el motivo',
    comparacion: 'Comparación de puntajes', riesgo: 'Riesgo', de100: 'de 100', fuente: 'Fuente', cargando: 'Leyendo los satélites de la NASA…',
  },
  en: {
    sub: 'Powered by NASA satellite data',
    queHago: 'What do I do?', queSiembro: 'What to plant?', mapa: 'Map', funciona: 'Does it work?', ayuda: 'Help',
    buscar: 'Search any place in the world…', miUbicacion: 'Use my location', nivelRiesgo: 'Risk level',
    alto: 'High', medio: 'Medium', bajo: 'Low', miParcela: 'My plot', coordenadas: 'Coordinates', analizar: 'Analyze this plot',
    queHagoAhora: 'What do I do now?', accion2sem: 'The action for the next 2 weeks. The whole-season risk is in «What to plant?»',
    enQue: 'How can we help?', recomiendame: 'Recommend what to plant', recomiendameSub: 'We tell you which seasonal crop suits your plot',
    tengoPermanente: 'I already have a perennial crop', tengoPermanenteSub: 'Mango, lime, banana, etc.',
    cambiarParcela: 'Change plot', alerta: 'Alert', accionRec: 'Recommended action', riesgoClim: 'Climate risk', motivo: 'Reason',
    dato: 'Data', siembraPlaneada: 'Planned sowing', cambiar: 'Change', whatsapp: 'Share on WhatsApp', mejorRot: 'Best rotation',
    pregunta: 'Ask AllpaShift', preguntaSub: 'Get answers about this recommendation',
    satelites: 'What the satellites see', satelitesSub: 'Tap an indicator to see why',
    queConviene: 'What should I plant?', tocaTarjeta: 'Tap a card to see why it has that score', cuando: 'When will you plant?',
    esteMes: 'This month', proximo: 'Next month', en2: 'In 2 months',
    aviso: 'AllpaShift does not forecast exact weather months ahead. It estimates season risk by combining NASA climate history with early signals such as El Niño.',
    recomendada: 'Recommended', usoAgua: 'Water use', porQue: 'Why this score?', perspectiva: 'Season outlook',
    siembra: 'Sowing', cosecha: 'Harvest', duracion: 'Duration', meses: 'months', masRiesgoso: 'Riskiest month', tocaMes: 'Tap a month to see why',
    comparacion: 'Score comparison', riesgo: 'Risk', de100: 'of 100', fuente: 'Source', cargando: 'Reading NASA satellites…',
  },
} as const

export type Clave = keyof typeof T.es
export function t(k: Clave): string { return T[estado.idioma][k] }
