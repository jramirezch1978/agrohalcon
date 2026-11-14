<script setup lang="ts">
import { ArrowRight, MapPinned } from 'lucide-vue-next'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import type { ZonaRiesgo } from '@/types/api'

defineProps<{ zona: ZonaRiesgo }>()
defineEmits<{ ver: [] }>()
</script>

<template>
  <div class="w-56 font-sans text-tinta dark:text-white">
    <p class="flex items-center gap-1.5 text-[11px] font-bold tracking-[0.12em] text-stone-500 uppercase">
      <MapPinned class="size-3.5" aria-hidden="true" />{{ $t('mapa.zona') }}
    </p>
    <p class="mt-1 font-display text-xl leading-tight font-bold tracking-tight">{{ zona.nombre }}</p>
    <RiskBadge v-if="zona.nivel" class="mt-2" :nivel="zona.nivel" con-titulo tamano="md" />
    <p v-else class="mt-2 text-sm font-semibold text-stone-500">{{ $t('mapa.sinDato') }}</p>
    <button
      type="button"
      class="mt-4 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-agro-700 px-4 text-sm font-semibold text-white transition hover:bg-agro-800 active:scale-[0.98] dark:bg-agro-600"
      @click="$emit('ver')"
    >
      {{ $t('acciones.verRecomendacion') }}<ArrowRight class="size-4" aria-hidden="true" />
    </button>
  </div>
</template>
