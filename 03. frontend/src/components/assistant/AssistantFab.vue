<script setup lang="ts">
import { Sparkles } from 'lucide-vue-next'
import { useAsistenteStore } from '@/stores/asistente'

const chat = useAsistenteStore()
</script>

<template>
  <!-- Bolita flotante: no tapa el contenido; el texto va como etiqueta accesible y como tooltip -->
  <button
    type="button"
    aria-haspopup="dialog"
    :aria-expanded="chat.panelAbierto"
    :aria-label="$t('asistente.abrir')"
    :title="$t('asistente.abrir')"
    class="fixed right-4 bottom-[calc(6.5rem+env(safe-area-inset-bottom))] z-[600] grid size-14 place-items-center rounded-full bg-tinta text-brote-300 shadow-glow ring-4 ring-brote-400 transition hover:scale-105 active:scale-95 lg:right-8 lg:bottom-8 dark:ring-brote-400"
    @click="chat.abrirPanel()"
  >
    <Sparkles class="size-6" aria-hidden="true" />
  </button>
</template>
