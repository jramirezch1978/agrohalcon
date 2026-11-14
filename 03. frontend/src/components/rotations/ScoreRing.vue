<script setup lang="ts">
import { computed, toRef } from 'vue'
import { useContador, useMontado } from '@/composables/useAnimacion'
import { ESTILO_RIESGO } from '@/composables/useRiesgo'
import type { NivelRiesgo } from '@/types/api'

const props = withDefaults(defineProps<{ puntaje: number; nivel: NivelRiesgo; tamano?: number; retraso?: number; sobreOscuro?: boolean }>(), {
  tamano: 128,
  retraso: 0,
  sobreOscuro: false,
})

// Anillo SVG: se llena y el número sube al cargar
const R = 52
const C = 2 * Math.PI * R
const montado = useMontado(150 + props.retraso)
const numero = useContador(toRef(() => props.puntaje), 1200, 150 + props.retraso)
const largo = computed(() => (montado.value ? (Math.max(0, Math.min(100, props.puntaje)) / 100) * C : 0))
</script>

<template>
  <div class="relative shrink-0" :style="{ width: tamano + 'px', height: tamano + 'px' }" role="img" :aria-label="`${$t('rotaciones.puntaje')}: ${puntaje} ${$t('rotaciones.de100')}`">
    <svg viewBox="0 0 120 120" class="size-full -rotate-90" aria-hidden="true">
      <circle cx="60" cy="60" :r="R" fill="none" stroke-width="10" :class="sobreOscuro ? 'stroke-white/12' : 'stroke-tinta/7 dark:stroke-white/10'" />
      <circle
        cx="60"
        cy="60"
        :r="R"
        fill="none"
        stroke-width="10"
        stroke-linecap="round"
        :stroke="ESTILO_RIESGO[nivel].hex"
        :stroke-dasharray="`${largo} ${C}`"
        class="transition-[stroke-dasharray] duration-[1200ms] ease-out"
      />
    </svg>
    <div class="absolute inset-0 flex flex-col items-center justify-center">
      <span class="font-display leading-none font-extrabold tracking-tight tabular-nums" :style="{ fontSize: tamano * 0.3 + 'px' }">{{ Math.round(numero) }}</span>
      <span class="mt-0.5 text-[11px] font-medium" :class="sobreOscuro ? 'text-white/70' : 'text-stone-500 dark:text-stone-400'">{{ $t('rotaciones.de100') }}</span>
    </div>
  </div>
</template>
