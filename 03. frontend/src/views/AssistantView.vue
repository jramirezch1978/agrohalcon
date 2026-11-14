<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatPanel from '@/components/assistant/ChatPanel.vue'
import { useAsistenteStore } from '@/stores/asistente'

const chat = useAsistenteStore()
const route = useRoute()
const router = useRouter()

onMounted(() => {
  // Permite abrir con una pregunta: #/asistente?q=...
  const q = route.query.q
  if (typeof q === 'string' && q) {
    router.replace({ query: {} })
    chat.preguntar(q)
  }
})
</script>

<template>
  <section
    class="mx-auto flex h-[calc(100dvh-4rem-5.5rem-env(safe-area-inset-top)-env(safe-area-inset-bottom))] max-w-2xl flex-col px-3 pt-2 pb-3 lg:h-dvh lg:px-10 lg:py-8"
  >
    <h1 class="sr-only">{{ $t('asistente.titulo') }}</h1>
    <ChatPanel class="superficie min-h-0 flex-1 overflow-hidden" />
  </section>
</template>
