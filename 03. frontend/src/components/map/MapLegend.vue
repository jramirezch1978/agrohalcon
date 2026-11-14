<script setup lang="ts">
import RiskBadge from '@/components/ui/RiskBadge.vue'
import type { NivelRiesgo } from '@/types/api'

const NIVELES: NivelRiesgo[] = ['alto', 'medio', 'bajo']
</script>

<template>
  <aside class="superficie !rounded-2xl p-3 shadow-float" :aria-label="$t('riesgo.leyenda')">
    <p class="mb-2 text-[11px] font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">{{ $t('riesgo.leyenda') }}</p>
    <ul class="flex flex-col gap-1.5">
      <li v-for="n in NIVELES" :key="n"><RiskBadge :nivel="n" /></li>
    </ul>
  </aside>
</template>
