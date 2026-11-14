<script setup lang="ts">
import { Satellite } from 'lucide-vue-next'

withDefaults(defineProps<{ fuente: string; sobreOscuro?: boolean; corta?: boolean }>(), {
  sobreOscuro: false,
  corta: false,
})
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold"
    :class="
      sobreOscuro
        ? 'bg-white/10 text-white ring-1 ring-white/15 backdrop-blur-sm'
        : 'bg-nasa-50 text-nasa-800 ring-1 ring-nasa-200 dark:bg-nasa-400/10 dark:text-nasa-200 dark:ring-nasa-400/20'
    "
  >
    <Satellite class="size-3.5" aria-hidden="true" />
    {{ corta ? fuente : $t('inicio.fuente', { fuente }) }}
  </span>
</template>
