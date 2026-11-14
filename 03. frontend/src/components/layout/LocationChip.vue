<script setup lang="ts">
import { ChevronDown, MapPin } from 'lucide-vue-next'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const { t } = useI18n()
const nombre = computed(() => {
  const p = store.parcela
  if (!p) return t('acciones.elegirParcela')
  return p.nombre ?? `${p.lat.toFixed(2)}, ${p.lon.toFixed(2)}`
})
</script>

<template>
  <RouterLink
    to="/mapa"
    :aria-label="`${$t('acciones.cambiarUbicacion')}: ${nombre}`"
    class="group flex min-w-0 items-center gap-2 rounded-full py-1.5 pr-3 pl-1.5 transition hover:bg-tinta/5 dark:hover:bg-white/8"
  >
    <span class="grid size-8 shrink-0 place-items-center rounded-full bg-agro-700 text-white dark:bg-brote-400 dark:text-tinta">
      <MapPin class="size-4" aria-hidden="true" />
    </span>
    <span class="truncate text-sm font-semibold">{{ nombre }}</span>
    <ChevronDown class="size-4 shrink-0 text-stone-400 transition group-hover:translate-y-0.5" aria-hidden="true" />
  </RouterLink>
</template>
