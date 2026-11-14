<script setup lang="ts">
import AppLogo from '@/components/ui/AppLogo.vue'
import LocationChip from './LocationChip.vue'
import { NAV_ITEMS } from './NavItems'
import PreferencesControls from './PreferencesControls.vue'
</script>

<template>
  <aside class="fixed inset-y-0 left-0 z-[500] hidden w-72 flex-col p-4 lg:flex">
    <div class="bosque flex h-full flex-col rounded-[28px] p-5 text-white shadow-float">
      <RouterLink to="/hoy" class="flex items-center gap-3">
        <AppLogo :tamano="42" />
        <span>
          <span class="block font-display text-xl font-extrabold tracking-tight">AllpaShift</span>
          <span class="block text-xs text-white/60">{{ $t('app.datosNasa') }}</span>
        </span>
      </RouterLink>

      <nav :aria-label="$t('nav.principal')" class="mt-10">
        <ul class="space-y-1">
          <li v-for="item in NAV_ITEMS" :key="item.to">
            <RouterLink
              :to="item.to"
              class="flex items-center gap-3 rounded-2xl px-4 py-3 text-[15px] font-medium text-white/70 transition hover:bg-white/8 hover:text-white"
              active-class="!bg-brote-400 !text-tinta font-semibold shadow-glow"
            >
              <component :is="item.icono" class="size-5" aria-hidden="true" />
              {{ $t(item.clave) }}
            </RouterLink>
          </li>
        </ul>
      </nav>

      <div class="mt-auto space-y-3">
        <div class="rounded-2xl bg-white/8 p-1 text-white ring-1 ring-white/10 [&_a:hover]:bg-white/10 [&_span.truncate]:text-white">
          <LocationChip />
        </div>
        <div class="flex justify-center rounded-2xl bg-white p-1.5 text-tinta dark:bg-noche-2 dark:text-white">
          <PreferencesControls />
        </div>
      </div>
    </div>
  </aside>
</template>
