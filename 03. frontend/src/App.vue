<script setup lang="ts">
import { computed, watchEffect } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import AssistantFab from '@/components/assistant/AssistantFab.vue'
import AssistantSheet from '@/components/assistant/AssistantSheet.vue'
import AppToasts from '@/components/layout/AppToasts.vue'
import BottomNav from '@/components/layout/BottomNav.vue'
import DataModeBanner from '@/components/layout/DataModeBanner.vue'
import SideBar from '@/components/layout/SideBar.vue'
import TopBar from '@/components/layout/TopBar.vue'
import { useAppStore } from '@/stores/app'
import { useAsistenteStore } from '@/stores/asistente'

const route = useRoute()
const store = useAppStore()
const chat = useAsistenteStore()
const { t } = useI18n()
const conNav = computed(() => !route.meta.sinNav)
const completa = computed(() => !!route.meta.completa)
const conFab = computed(() => !!route.meta.fabAsistente && !!store.parcela)

watchEffect(() => {
  const clave = route.meta.titulo as string | undefined
  document.title = clave ? `${t(clave)} · AllpaShift` : 'AllpaShift'
})
</script>

<template>
  <div class="min-h-dvh">
    <!-- Aviso fijo si hay datos de ejemplo en pantalla + avisos al cambiar de fuente -->
    <DataModeBanner />
    <AppToasts />
    <template v-if="conNav">
      <SideBar />
      <TopBar />
      <BottomNav />
    </template>
    <div :class="conNav && 'lg:pl-72'">
      <main
        :class="
          completa
            ? 'relative'
            : conNav
              ? ['mx-auto max-w-5xl px-4 pt-3 sm:px-6 lg:px-10 lg:pt-10', conFab ? 'pb-48 lg:pb-32' : 'pb-32 lg:pb-12']
              : ''
        "
      >
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </RouterView>
      </main>
    </div>

    <!-- Asistente: botón flotante en /hoy y /campana, panel disponible en toda la app -->
    <Transition enter-from-class="scale-75 opacity-0" leave-to-class="scale-75 opacity-0" enter-active-class="transition duration-300" leave-active-class="transition duration-150">
      <AssistantFab v-if="conFab && !chat.panelAbierto" />
    </Transition>
    <AssistantSheet />
  </div>
</template>
