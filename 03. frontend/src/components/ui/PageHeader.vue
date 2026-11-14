<script setup lang="ts">
defineProps<{ titulo: string; subtitulo?: string; etiqueta?: string }>()
</script>

<template>
  <header class="stagger mb-6">
    <p v-if="etiqueta" class="mb-2 text-xs font-bold tracking-[0.14em] text-agro-600 uppercase dark:text-brote-400">{{ etiqueta }}</p>
    <h1 class="font-display text-[32px] leading-[1.05] font-extrabold tracking-tight text-balance sm:text-4xl">{{ titulo }}</h1>
    <p v-if="subtitulo" class="mt-2 max-w-xl text-[15px] text-stone-600 dark:text-stone-400">{{ subtitulo }}</p>
    <slot />
  </header>
</template>
