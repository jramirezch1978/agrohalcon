<script setup lang="ts">
import type { Component } from 'vue'

withDefaults(
  defineProps<{
    variante?: 'primario' | 'acento' | 'secundario' | 'fantasma' | 'whatsapp' | 'vidrio'
    tamano?: 'md' | 'lg'
    icono?: Component
    iconoDerecha?: Component
    bloque?: boolean
    cargando?: boolean
    type?: 'button' | 'submit'
  }>(),
  { variante: 'primario', tamano: 'lg', bloque: false, cargando: false, type: 'button' },
)
</script>

<template>
  <button
    :type="type"
    :disabled="cargando"
    :aria-busy="cargando"
    class="inline-flex items-center justify-center gap-2 rounded-2xl font-semibold whitespace-nowrap transition duration-200 active:scale-[0.97] disabled:cursor-wait disabled:opacity-70"
    :class="[
      tamano === 'lg' ? 'min-h-14 px-6 text-[15px]' : 'min-h-11 px-4 text-sm',
      bloque && 'w-full',
      {
        primario: 'bg-agro-700 text-white shadow-[0_6px_20px_-6px_rgb(25_97_58/0.6)] hover:bg-agro-800 dark:bg-agro-600 dark:hover:bg-agro-500',
        acento: 'bg-brote-400 text-tinta shadow-glow hover:bg-brote-300',
        secundario: 'bg-white text-tinta ring-1 ring-tinta/10 hover:bg-arena dark:bg-noche-3 dark:text-white dark:ring-white/10 dark:hover:bg-white/10',
        fantasma: 'text-agro-700 hover:bg-agro-50 dark:text-brote-300 dark:hover:bg-white/5',
        whatsapp: 'bg-[#128c4a] text-white shadow-[0_6px_20px_-6px_rgb(18_140_74/0.6)] hover:bg-[#0f7a40]',
        vidrio: 'bg-white/10 text-white ring-1 ring-white/15 backdrop-blur-md hover:bg-white/20',
      }[variante],
    ]"
  >
    <span v-if="cargando" class="size-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
    <component :is="icono" v-else-if="icono" class="size-5 shrink-0" aria-hidden="true" />
    <slot />
    <component :is="iconoDerecha" v-if="iconoDerecha" class="size-5 shrink-0" aria-hidden="true" />
  </button>
</template>
