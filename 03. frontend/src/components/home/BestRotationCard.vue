<script setup lang="ts">
import { ArrowRight, Sprout } from 'lucide-vue-next'
import { computed } from 'vue'
import { calificacionDe, NIVEL_CALIFICACION } from '@/composables/useRotacion'
import { ESTILO_RIESGO } from '@/composables/useRiesgo'
import type { Rotacion } from '@/types/api'

const props = defineProps<{ rotacion: Rotacion }>()
const calif = computed(() => calificacionDe(props.rotacion))
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
      <p class="truncate text-sm text-stone-500 dark:text-stone-400">{{ rotacion.explicacion }}</p>
    </div>
    <ArrowRight class="size-5 shrink-0 text-stone-400 transition group-hover:translate-x-1" aria-hidden="true" />
  </RouterLink>
</template>
