<script setup lang="ts">
import AppLogo from '@/components/ui/AppLogo.vue'
import LocationChip from './LocationChip.vue'
import PreferencesControls from './PreferencesControls.vue'
</script>

<template>
  <header
    class="sticky top-0 z-[500] bg-arena/80 backdrop-blur-xl lg:hidden dark:bg-noche/80"
    style="padding-top: env(safe-area-inset-top)"
  >
    <div class="flex h-16 items-center gap-1 px-3">
      <RouterLink to="/hoy" class="shrink-0 rounded-xl p-1" aria-label="AgroShift">
        <AppLogo :tamano="34" />
      </RouterLink>
      <LocationChip class="mr-auto" />
      <PreferencesControls />
    </div>
  </header>
</template>
