<script setup lang="ts">
import AppLogo from '@/components/ui/AppLogo.vue'
</script>

<template>
  <div class="flex items-end gap-2" role="status">
    <AppLogo :tamano="30" class="mb-0.5 shrink-0" />
    <div class="flex items-center gap-1.5 rounded-[22px] rounded-bl-md bg-white px-5 py-4 shadow-card ring-1 ring-tinta/5 dark:bg-noche-3 dark:ring-white/8">
      <span v-for="i in 3" :key="i" class="size-2 animate-blink rounded-full bg-agro-600 dark:bg-brote-400" :style="{ animationDelay: `${i * 0.15}s` }" aria-hidden="true" />
      <span class="sr-only">{{ $t('asistente.escribiendo') }}</span>
    </div>
  </div>
</template>
