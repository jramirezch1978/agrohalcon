<script setup lang="ts">
import { NAV_ITEMS } from './NavItems'
</script>

<template>
  <nav
    :aria-label="$t('nav.principal')"
    class="fixed inset-x-0 bottom-0 z-[500] px-3 lg:hidden"
    style="padding-bottom: max(0.75rem, env(safe-area-inset-bottom))"
  >
    <ul class="mx-auto grid max-w-md grid-cols-5 gap-1 rounded-[26px] bg-tinta/95 p-1.5 shadow-float ring-1 ring-white/10 backdrop-blur-xl dark:bg-noche-3/95">
      <li v-for="item in NAV_ITEMS" :key="item.to">
        <RouterLink :to="item.to" custom v-slot="{ href, navigate, isActive }">
          <a
            :href="href"
            :aria-current="isActive ? 'page' : undefined"
            class="relative flex h-14 flex-col items-center justify-center gap-0.5 rounded-[20px] text-[10.5px] leading-tight font-semibold transition duration-200 active:scale-95"
            :class="isActive ? 'bg-brote-400 text-tinta' : 'text-stone-300 hover:bg-white/8 hover:text-white'"
            @click="navigate"
          >
            <component :is="item.icono" class="size-[22px]" :stroke-width="isActive ? 2.4 : 2" aria-hidden="true" />
            <span>{{ $t(item.clave) }}</span>
          </a>
        </RouterLink>
      </li>
    </ul>
  </nav>
</template>
