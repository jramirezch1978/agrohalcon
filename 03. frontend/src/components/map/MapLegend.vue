<script setup lang="ts">
import { Waves } from 'lucide-vue-next'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import type { MapaRiesgo, NivelRiesgo } from '@/types/api'

/**
 * Leyenda del mapa. El color de cada valle es su riesgo LOCAL (lluvia, humedad del suelo, calor).
 * El Niño es el mismo para toda la costa: se muestra aparte aquí, no pinta los valles.
 */
defineProps<{ elNino?: MapaRiesgo['elNino'] }>()
const NIVELES: NivelRiesgo[] = ['alto', 'medio', 'bajo']
</script>

<template>
  <aside class="superficie max-w-[11rem] !rounded-2xl p-3 shadow-float" :aria-label="$t('riesgo.leyenda')">
    <p class="mb-2 text-[11px] font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">{{ $t('riesgo.leyenda') }}</p>
    <ul class="flex flex-col gap-1.5">
      <li v-for="n in NIVELES" :key="n"><RiskBadge :nivel="n" /></li>
    </ul>
    <div v-if="elNino && elNino.nivel !== 'bajo'" class="mt-3 border-t border-tinta/10 pt-2.5 dark:border-white/10">
      <p class="flex items-center gap-1.5 text-xs font-bold text-red-700 dark:text-red-300">
        <Waves class="size-4 shrink-0" aria-hidden="true" />{{ $t('mapa.elNinoTitulo', { valor: `${elNino.valor > 0 ? '+' : ''}${elNino.valor}` }) }}
      </p>
      <p class="mt-1 text-[11px] leading-snug text-stone-600 dark:text-stone-300">{{ $t('mapa.elNinoTexto', { fuente: elNino.fuente }) }}</p>
    </div>
  </aside>
</template>
