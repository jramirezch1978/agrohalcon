<script setup lang="ts">
import { Info } from 'lucide-vue-next'
</script>

<template>
  <p class="flex items-start gap-2 rounded-2xl bg-nasa-50 px-4 py-3 text-xs leading-relaxed text-nasa-900 ring-1 ring-nasa-200 dark:bg-nasa-400/10 dark:text-nasa-100 dark:ring-nasa-400/20">
    <Info class="mt-px size-4 shrink-0" aria-hidden="true" />{{ $t('campana.aviso') }}
  </p>
</template>
