<script setup lang="ts">
import { ArrowRight, CloudSun, Droplets, Leaf, Sprout } from 'lucide-vue-next'
import { computed } from 'vue'
import { calificacionDe, NIVEL_CALIFICACION } from '@/composables/useRotacion'
import { ESTILO_RIESGO } from '@/composables/useRiesgo'
import type { Rotacion } from '@/types/api'

const props = defineProps<{ rotacion: Rotacion }>()
/** Lo que lee el agricultor en el anillo: buena / regular / riesgosa */
const calif = computed(() => calificacionDe(props.rotacion))

/** Lo mejor que la rotación hace por el suelo (la regla que más suma), para que se vea en la portada */
const razonSuelo = computed(() => {
  const mas = (props.rotacion.descuentosSuelo ?? []).filter((d) => d.puntos > 0).sort((a, b) => b.puntos - a.puntos)
  return mas[0]?.explicacion
})
/** Aviso cuando la rotación gasta mucho agua (puntaje de agua bajo) */
const aguaBaja = computed(() => props.rotacion.puntajeAgua != null && props.rotacion.puntajeAgua <= 30)
/** Clima · suelo · agua: solo si el cálculo trae los tres puntajes */
const tresPuntajes = computed(() => props.rotacion.saludSuelo != null && props.rotacion.riesgoClimatico != null)
</script>

<template>
  <RouterLink to="/campana" class="superficie group flex items-center gap-4 p-5 transition hover:-translate-y-0.5 hover:shadow-float">
    <div class="relative grid size-16 shrink-0 place-items-center">
      <svg viewBox="0 0 36 36" class="absolute inset-0 -rotate-90" aria-hidden="true">
        <circle cx="18" cy="18" r="15.5" fill="none" stroke="currentColor" stroke-width="3.5" class="text-tinta/6 dark:text-white/8" />
        <circle
          cx="18" cy="18" r="15.5" fill="none" :stroke="ESTILO_RIESGO[NIVEL_CALIFICACION[calif]].hex" stroke-width="3.5" stroke-linecap="round"
          :stroke-dasharray="`${(rotacion.puntaje / 100) * 97.4} 97.4`"
        />
      </svg>
      <span class="font-display text-[13px] leading-tight font-bold">{{ $t(`calificacion.${calif}`) }}</span>
    </div>
    <div class="min-w-0 flex-1">
      <p class="flex items-center gap-1 text-xs font-bold tracking-[0.12em] text-agro-600 uppercase dark:text-brote-400">
        <Sprout class="size-3.5" aria-hidden="true" />{{ $t('inicio.mejorRotacion') }}
      </p>
      <p class="font-display text-lg font-bold tracking-tight">{{ rotacion.nombre }}</p>

      <!-- Clima · suelo · agua: el suelo también decide la recomendación -->
      <p v-if="tresPuntajes" class="mt-1 flex flex-wrap gap-1.5 text-xs font-semibold tabular-nums">
        <span class="inline-flex items-center gap-1 rounded-full bg-arena px-2 py-0.5 dark:bg-white/8">
          <CloudSun class="size-3.5" aria-hidden="true" />{{ $t('rotaciones.clima') }} {{ rotacion.riesgoClimatico }}
        </span>
        <span class="inline-flex items-center gap-1 rounded-full bg-agro-100 px-2 py-0.5 text-agro-800 dark:bg-agro-400/15 dark:text-agro-200">
          <Leaf class="size-3.5" aria-hidden="true" />{{ $t('rotaciones.suelo') }} {{ rotacion.saludSuelo }}
        </span>
        <span v-if="rotacion.puntajeAgua != null" class="inline-flex items-center gap-1 rounded-full bg-arena px-2 py-0.5 dark:bg-white/8">
          <Droplets class="size-3.5" aria-hidden="true" />{{ $t('prioridad.agua') }} {{ rotacion.puntajeAgua }}
        </span>
      </p>
      <p v-if="razonSuelo" class="mt-1.5 line-clamp-2 text-sm leading-snug text-agro-800 dark:text-agro-200">🌱 {{ razonSuelo }}</p>
      <p v-if="aguaBaja" class="mt-1.5 text-sm leading-snug font-semibold text-amber-700 dark:text-amber-300">💧 {{ $t('rotaciones.avisoAguaBaja', { n: rotacion.puntajeAgua }) }}</p>
      <p class="mt-1 line-clamp-2 text-sm leading-snug text-stone-500 dark:text-stone-400">{{ rotacion.motivoRecomendada ?? rotacion.explicacion }}</p>
    </div>
    <ArrowRight class="size-5 shrink-0 text-stone-400 transition group-hover:translate-x-1" aria-hidden="true" />
  </RouterLink>
</template>
