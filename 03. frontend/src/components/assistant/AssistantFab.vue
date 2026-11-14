<script setup lang="ts">
import { Sparkles } from 'lucide-vue-next'
import { useAsistenteStore } from '@/stores/asistente'

const chat = useAsistenteStore()
</script>

<template>
  <button
    type="button"
    aria-haspopup="dialog"
    :aria-expanded="chat.panelAbierto"
    class="fixed right-4 bottom-[calc(6.5rem+env(safe-area-inset-bottom))] z-[600] flex min-h-14 items-center gap-2 rounded-full bg-brote-400 py-2 pr-5 pl-2 font-semibold text-tinta shadow-glow ring-4 ring-arena transition hover:bg-brote-300 active:scale-95 lg:right-8 lg:bottom-8 dark:ring-noche"
    @click="chat.abrirPanel()"
  >
    <span class="grid size-10 place-items-center rounded-full bg-tinta text-brote-300">
      <Sparkles class="size-5" aria-hidden="true" />
    </span>
    <span class="text-[15px]">{{ $t('asistente.abrir') }}</span>
  </button>
</template>
