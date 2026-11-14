<script setup lang="ts">
import { MapPinned } from 'lucide-vue-next'

defineProps<{ titulo?: string; texto?: string }>()
</script>

<template>
  <div class="flex flex-col items-center gap-3 rounded-3xl border-2 border-dashed border-tinta/10 px-6 py-14 text-center dark:border-white/10">
    <div class="grid size-16 place-items-center rounded-full bg-agro-100 text-agro-700 dark:bg-agro-400/10 dark:text-brote-300">
      <MapPinned class="size-7" aria-hidden="true" />
    </div>
    <p class="font-display text-xl font-bold">{{ titulo || $t('estados.vacio') }}</p>
    <p class="max-w-xs text-sm text-stone-600 dark:text-stone-400">{{ texto || $t('estados.vacioTexto') }}</p>
    <slot />
  </div>
</template>
