<script setup lang="ts">
import { TriangleAlert, WifiOff } from 'lucide-vue-next'

withDefaults(defineProps<{ tono?: 'alto' | 'offline'; titulo?: string }>(), { tono: 'alto' })
</script>

<template>
  <div
    role="status"
    class="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm"
    :class="
      tono === 'alto'
        ? 'bg-red-600 text-white shadow-[0_8px_24px_-8px_rgb(220_38_38/0.6)]'
        : 'bg-nasa-50 text-nasa-900 ring-1 ring-nasa-200 dark:bg-nasa-400/10 dark:text-nasa-100 dark:ring-nasa-400/20'
    "
  >
    <span
      class="grid size-9 shrink-0 place-items-center rounded-xl"
      :class="tono === 'alto' ? 'bg-white/15' : 'bg-nasa-100 dark:bg-nasa-400/15'"
    >
      <TriangleAlert v-if="tono === 'alto'" class="size-5" aria-hidden="true" />
      <WifiOff v-else class="size-5" aria-hidden="true" />
    </span>
    <p class="leading-snug">
      <strong v-if="titulo" class="block font-semibold">{{ titulo }}</strong>
      <span :class="titulo && 'opacity-90'"><slot /></span>
    </p>
  </div>
</template>
