<script setup lang="ts">
import { X } from 'lucide-vue-next'
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps<{ abierto: boolean; titulo?: string }>()
const emit = defineEmits<{ cerrar: [] }>()
const panel = ref<HTMLElement>()

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('cerrar')
}

watch(
  () => props.abierto,
  async (v) => {
    document.body.style.overflow = v ? 'hidden' : ''
    if (v) {
      window.addEventListener('keydown', onKey)
      await nextTick()
      panel.value?.focus()
    } else {
      window.removeEventListener('keydown', onKey)
    }
  },
)
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="abierto" class="fixed inset-0 z-[1000] flex items-end justify-center md:items-center md:p-6">
        <div class="absolute inset-0 bg-noche/50 backdrop-blur-[2px]" @click="emit('cerrar')" />
        <div
          ref="panel"
          role="dialog"
          aria-modal="true"
          :aria-label="titulo"
          tabindex="-1"
          class="sheet-panel relative max-h-[88dvh] w-full overflow-y-auto rounded-t-[28px] bg-white p-6 pt-3 shadow-float outline-none md:max-w-lg md:rounded-[28px] md:pt-6 dark:bg-noche-2"
          style="padding-bottom: max(1.5rem, env(safe-area-inset-bottom))"
        >
          <div class="mx-auto mb-4 h-1.5 w-10 rounded-full bg-tinta/15 md:hidden dark:bg-white/20" aria-hidden="true" />
          <button
            type="button"
            :aria-label="$t('acciones.cerrar')"
            class="absolute top-4 right-4 grid size-10 place-items-center rounded-full bg-arena text-tinta transition hover:bg-arena-2 dark:bg-white/10 dark:text-white"
            @click="emit('cerrar')"
          >
            <X class="size-5" aria-hidden="true" />
          </button>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
