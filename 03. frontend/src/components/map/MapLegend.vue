<script setup lang="ts">
import { Info, Waves, X } from 'lucide-vue-next'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import type { MapaRiesgo, NivelRiesgo } from '@/types/api'

/**
 * Leyenda del mapa, plegable (cerrada ocupa solo un botón redondo y no tapa el mapa en el celular).
 * El color de cada valle es su riesgo LOCAL (lluvia, humedad del suelo, calor).
 * El Niño es el mismo para toda la costa: se muestra aparte aquí, no pinta los valles.
 */
defineProps<{ elNino?: MapaRiesgo['elNino'] }>()
const abierta = defineModel<boolean>('abierta', { default: false })
const NIVELES: NivelRiesgo[] = ['alto', 'medio', 'bajo']
</script>

<template>
  <div>
    <button
      v-if="!abierta"
      type="button"
      :aria-label="$t('riesgo.leyenda')"
      :title="$t('riesgo.leyenda')"
      aria-expanded="false"
      class="relative grid size-12 place-items-center rounded-full bg-white text-tinta shadow-float transition active:scale-95 dark:bg-noche-2 dark:text-white"
      @click="abierta = true"
    >
      <Info class="size-5" aria-hidden="true" />
      <span v-if="elNino && elNino.nivel !== 'bajo'" class="absolute -top-0.5 -right-0.5 size-3.5 rounded-full bg-red-600 ring-2 ring-white dark:ring-noche-2" aria-hidden="true" />
    </button>
    <aside v-else class="superficie max-w-[11rem] !rounded-2xl p-3 shadow-float" :aria-label="$t('riesgo.leyenda')">
      <div class="mb-2 flex items-center justify-between gap-2">
        <p class="text-xs font-bold tracking-[0.12em] text-stone-500 uppercase dark:text-stone-400">{{ $t('riesgo.leyenda') }}</p>
        <button type="button" :aria-label="$t('acciones.cerrar')" aria-expanded="true" class="-m-1.5 grid size-8 shrink-0 place-items-center rounded-full hover:bg-tinta/5 dark:hover:bg-white/8" @click="abierta = false">
          <X class="size-4" aria-hidden="true" />
        </button>
      </div>
      <ul class="flex flex-col gap-1.5">
        <li v-for="n in NIVELES" :key="n"><RiskBadge :nivel="n" /></li>
      </ul>
      <div v-if="elNino && elNino.nivel !== 'bajo'" class="mt-3 border-t border-tinta/10 pt-2.5 dark:border-white/10">
        <p class="flex items-center gap-1.5 text-xs font-bold text-red-700 dark:text-red-300">
          <Waves class="size-4 shrink-0" aria-hidden="true" />{{ $t('mapa.elNinoTitulo', { valor: `${elNino.valor > 0 ? '+' : ''}${elNino.valor}` }) }}
        </p>
        <p class="mt-1 text-xs leading-snug text-stone-600 dark:text-stone-300">{{ $t('mapa.elNinoTexto', { fuente: elNino.fuente }) }}</p>
      </div>
    </aside>
  </div>
</template>
