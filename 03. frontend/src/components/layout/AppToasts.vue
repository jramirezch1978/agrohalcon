<script setup lang="ts">
import { TriangleAlert, X } from 'lucide-vue-next'
import { useOrigenStore } from '@/stores/origen'

/** Avisos cortos cuando la app cambia de fuente de datos (servicio caído, copia guardada…). */
const origen = useOrigenStore()
</script>

<template>
  <div class="pointer-events-none fixed inset-x-0 top-14 z-[700] flex flex-col items-center gap-2 px-4 lg:top-6 lg:left-72" aria-live="assertive">
    <TransitionGroup enter-from-class="-translate-y-3 opacity-0" leave-to-class="opacity-0" enter-active-class="transition duration-300" leave-active-class="transition duration-200">
      <div
        v-for="t in origen.toasts"
        :key="t.id"
        role="alert"
        class="pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-2xl bg-tinta px-4 py-3 text-sm font-medium text-white shadow-float ring-1 ring-white/10"
      >
        <TriangleAlert class="mt-0.5 size-5 shrink-0 text-amber-400" aria-hidden="true" />
        <span class="flex-1">{{ t.texto }}</span>
        <button type="button" class="-m-1 grid size-8 place-items-center rounded-full hover:bg-white/10" :aria-label="$t('acciones.cerrar')" @click="origen.cerrar(t.id)">
          <X class="size-4" aria-hidden="true" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
