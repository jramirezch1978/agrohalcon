<script setup lang="ts">
import { HandHeart, Info } from 'lucide-vue-next'
</script>

<template>
  <div class="space-y-2">
  <p class="flex items-start gap-2 rounded-2xl bg-nasa-50 px-4 py-3 text-xs leading-relaxed text-nasa-900 ring-1 ring-nasa-200 dark:bg-nasa-400/10 dark:text-nasa-100 dark:ring-nasa-400/20">
    <Info class="mt-px size-4 shrink-0" aria-hidden="true" />{{ $t('campana.aviso') }}
  </p>
  <p class="flex items-start gap-2 rounded-2xl bg-agro-50 px-4 py-3 text-xs leading-relaxed text-agro-900 ring-1 ring-agro-200 dark:bg-agro-400/10 dark:text-agro-100 dark:ring-agro-400/20">
    <HandHeart class="mt-px size-4 shrink-0" aria-hidden="true" />{{ $t('campana.apoyo') }}
  </p>
  </div>
</template>
