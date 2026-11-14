<script setup lang="ts">
withDefaults(defineProps<{ alto?: string; ancho?: string; redondo?: string; oscuro?: boolean }>(), {
  alto: 'h-4',
  ancho: 'w-full',
  redondo: 'rounded-lg',
  oscuro: false,
})
</script>

<template>
  <div
    aria-hidden="true"
    class="animate-shimmer bg-[length:200%_100%]"
    :class="[
      alto,
      ancho,
      redondo,
      oscuro
        ? 'bg-linear-to-r from-white/8 via-white/16 to-white/8'
        : 'bg-linear-to-r from-arena-2 via-arena to-arena-2 dark:from-white/5 dark:via-white/10 dark:to-white/5',
    ]"
  />
</template>
