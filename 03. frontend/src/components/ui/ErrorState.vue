<script setup lang="ts">
import { CloudOff, RotateCw } from 'lucide-vue-next'
import BaseButton from './BaseButton.vue'

defineProps<{ mensaje?: string }>()
defineEmits<{ reintentar: [] }>()
</script>

<template>
  <div role="alert" class="superficie flex flex-col items-center gap-4 px-6 py-12 text-center">
    <div class="relative grid size-16 place-items-center">
      <span class="absolute inset-0 rounded-full bg-red-500/10" />
      <CloudOff class="size-7 text-red-600 dark:text-red-400" aria-hidden="true" />
    </div>
    <div>
      <p class="font-display text-xl font-bold">{{ $t('estados.error') }}</p>
      <p class="mt-1 text-sm text-stone-600 dark:text-stone-400">{{ mensaje || $t('estados.errorRed') }}</p>
    </div>
    <BaseButton :icono="RotateCw" @click="$emit('reintentar')">{{ $t('acciones.reintentar') }}</BaseButton>
  </div>
</template>
