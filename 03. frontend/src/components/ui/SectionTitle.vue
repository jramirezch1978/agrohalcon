<script setup lang="ts">
defineProps<{ titulo: string; subtitulo?: string }>()
</script>

<template>
  <div class="flex items-end justify-between gap-3">
    <div>
      <h2 class="font-display text-lg font-bold tracking-tight">{{ titulo }}</h2>
      <p v-if="subtitulo" class="text-sm text-stone-500 dark:text-stone-400">{{ subtitulo }}</p>
    </div>
    <slot />
  </div>
</template>
