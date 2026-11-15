<script setup lang="ts">
import { Satellite } from 'lucide-vue-next'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
</script>

<template>
  <div class="space-y-4" aria-busy="true" role="status" :aria-label="$t('estados.descargandoNasa')">
    <p class="flex items-center gap-2 text-sm font-medium text-stone-600 dark:text-stone-300">
      <Satellite class="size-4 shrink-0 animate-pulse text-nasa-600 dark:text-nasa-300" aria-hidden="true" />{{ $t('estados.descargandoNasa') }}
    </p>
    <div class="bosque space-y-4 rounded-[30px] p-6 sm:p-8">
      <SkeletonBlock oscuro ancho="w-48" alto="h-6" redondo="rounded-full" />
      <SkeletonBlock oscuro alto="h-9" ancho="w-11/12" />
      <SkeletonBlock oscuro alto="h-9" ancho="w-2/3" />
      <SkeletonBlock oscuro alto="h-16" redondo="rounded-2xl" />
      <SkeletonBlock oscuro alto="h-7" ancho="w-28" redondo="rounded-full" />
    </div>
    <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <div v-for="i in 4" :key="i" class="superficie space-y-3 p-5">
        <div class="flex items-center gap-2">
          <SkeletonBlock alto="h-10" ancho="w-10" redondo="rounded-2xl" />
          <SkeletonBlock ancho="w-16" />
        </div>
        <SkeletonBlock alto="h-8" ancho="w-24" />
        <SkeletonBlock alto="h-3" ancho="w-20" />
        <SkeletonBlock alto="h-2.5" redondo="rounded-full" />
        <SkeletonBlock alto="h-6" ancho="w-28" redondo="rounded-full" />
      </div>
    </div>
  </div>
</template>
