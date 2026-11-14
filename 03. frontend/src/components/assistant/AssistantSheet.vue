<script setup lang="ts">
import { Maximize2, X } from 'lucide-vue-next'
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAsistenteStore } from '@/stores/asistente'
import ChatPanel from './ChatPanel.vue'

const chat = useAsistenteStore()
const router = useRouter()
const route = useRoute()
const panel = ref<InstanceType<typeof ChatPanel>>()

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') chat.cerrarPanel()
}
watch(
  () => chat.panelAbierto,
  async (v) => {
    document.body.style.overflow = v ? 'hidden' : ''
    if (v) {
      window.addEventListener('keydown', onKey)
      await nextTick()
      panel.value?.enfocar()
    } else window.removeEventListener('keydown', onKey)
  },
)
// Al navegar, cerrar el panel
watch(() => route.path, () => chat.cerrarPanel())
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

function pantallaCompleta() {
  chat.cerrarPanel()
  router.push('/asistente')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="chat">
      <div v-if="chat.panelAbierto" class="fixed inset-0 z-[1000] flex items-end justify-end lg:items-stretch">
        <div class="absolute inset-0 bg-noche/50 backdrop-blur-[2px]" @click="chat.cerrarPanel()" />
        <div
          role="dialog"
          aria-modal="true"
          :aria-label="$t('asistente.titulo')"
          class="chat-panel relative flex h-[90dvh] w-full flex-col overflow-hidden rounded-t-[28px] bg-white shadow-float lg:m-4 lg:h-auto lg:w-[440px] lg:rounded-[28px] dark:bg-noche-2"
          style="padding-bottom: env(safe-area-inset-bottom)"
        >
          <div class="mx-auto mt-2 h-1.5 w-10 shrink-0 rounded-full bg-tinta/15 lg:hidden dark:bg-white/20" aria-hidden="true" />
          <ChatPanel ref="panel" compacto class="min-h-0 flex-1">
            <template #acciones>
              <button type="button" :aria-label="$t('asistente.pantallaCompleta')" :title="$t('asistente.pantallaCompleta')" class="hidden size-10 place-items-center rounded-full hover:bg-arena sm:grid dark:hover:bg-white/8" @click="pantallaCompleta">
                <Maximize2 class="size-4" aria-hidden="true" />
              </button>
              <button type="button" :aria-label="$t('acciones.cerrar')" class="grid size-10 place-items-center rounded-full bg-arena hover:bg-arena-2 dark:bg-white/10" @click="chat.cerrarPanel()">
                <X class="size-5" aria-hidden="true" />
              </button>
            </template>
          </ChatPanel>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
