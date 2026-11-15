<script setup lang="ts">
import type { MotivoUbicacion } from '@/services/ubicacion'
import { ArrowLeft, ArrowRight, CloudRain, Crosshair, Map, Thermometer, Waves } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import PreferencesControls from '@/components/layout/PreferencesControls.vue'
import AppLogo from '@/components/ui/AppLogo.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const router = useRouter()
const paso = ref(1)
const errorUbicacion = ref<'' | MotivoUbicacion>('')

const claves = computed(() => `onboarding.paso${paso.value}`)

async function usarUbicacion() {
  errorUbicacion.value = ''
  const r = await store.pedirUbicacion()
  if (!r.ok) {
    errorUbicacion.value = r.motivo
    return
  }
  store.elegirParcela(r.coords)
  store.completarOnboarding()
  router.replace('/hoy')
}

function elegirMapa() {
  store.completarOnboarding()
  router.replace('/mapa')
}

function omitir() {
  store.completarOnboarding()
  router.replace('/hoy') // sin parcela, el router lleva al mapa
}

const SATELITES = [
  { icono: CloudRain, nombre: 'GPM', a: 0 },
  { icono: Thermometer, nombre: 'POWER', a: 120 },
  { icono: Waves, nombre: 'MUR', a: 240 },
]
</script>

<template>
  <section class="bosque flex min-h-dvh flex-col text-white" style="padding-top: env(safe-area-inset-top); padding-bottom: env(safe-area-inset-bottom)">
    <header class="flex items-center justify-between px-5 pt-4">
      <div class="flex items-center gap-2.5">
        <AppLogo :tamano="38" />
        <span class="font-display text-xl font-extrabold tracking-tight">AllpaShift</span>
      </div>
      <div class="rounded-full bg-white p-1 text-tinta dark:bg-noche-2 dark:text-white">
        <PreferencesControls />
      </div>
    </header>

    <!-- Ilustración -->
    <div class="relative mx-auto my-6 grid aspect-square w-full max-w-[340px] flex-1 place-items-center sm:max-h-[360px]" aria-hidden="true">
      <Transition mode="out-in" enter-from-class="opacity-0 scale-90" leave-to-class="opacity-0 scale-95" enter-active-class="transition duration-500 ease-out" leave-active-class="transition duration-200">
        <!-- Paso 1: planta creciendo con niveles de riesgo -->
        <div v-if="paso === 1" key="1" class="relative size-64">
          <div class="absolute inset-0 rounded-full bg-[radial-gradient(circle,rgb(194_238_92/0.25),transparent_65%)]" />
          <div class="absolute inset-8 rounded-full border border-white/10" />
          <div class="absolute inset-16 rounded-full border border-white/10" />
          <div class="absolute inset-0 grid place-items-center"><AppLogo :tamano="120" /></div>
          <span class="absolute top-6 left-2 rounded-full bg-emerald-500 px-3 py-1 text-xs font-bold shadow-float">● {{ $t('riesgo.bajo') }}</span>
          <span class="absolute top-24 -right-4 rounded-full bg-amber-500 px-3 py-1 text-xs font-bold text-tinta shadow-float">● {{ $t('riesgo.medio') }}</span>
          <span class="absolute bottom-6 left-6 rounded-full bg-red-500 px-3 py-1 text-xs font-bold shadow-float">● {{ $t('riesgo.alto') }}</span>
        </div>
        <!-- Paso 2: satélites en órbita -->
        <div v-else-if="paso === 2" key="2" class="relative size-72">
          <div class="absolute inset-[28%] rounded-full bg-[radial-gradient(circle_at_35%_30%,#4cb373,#123f29_60%,#082316)] shadow-[0_0_80px_20px_rgb(91_133_245/0.3)]" />
          <div class="absolute inset-[6%] rounded-full border border-dashed border-white/15" />
          <div class="absolute inset-0 animate-orbit">
            <div v-for="s in SATELITES" :key="s.nombre" class="absolute inset-[6%]" :style="{ transform: `rotate(${s.a}deg)` }">
              <span class="absolute top-0 left-1/2 grid size-12 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-2xl bg-white text-tinta shadow-float" :style="{ transform: `translate(-50%,-50%) rotate(${-s.a}deg)` }">
                <span class="grid animate-orbit place-items-center [animation-direction:reverse]"><component :is="s.icono" class="size-5" /></span>
              </span>
            </div>
          </div>
        </div>
        <!-- Paso 3: mapa con pin -->
        <div v-else key="3" class="relative size-64 overflow-hidden rounded-[40px] bg-[#e9e6db] shadow-float ring-8 ring-white/10">
          <svg viewBox="0 0 200 200" class="absolute inset-0 size-full">
            <path d="M0 140 C40 120 60 150 100 130 S160 90 200 100 V200 H0Z" fill="#b3e4c2" />
            <path d="M0 60 C30 70 70 40 110 60 S170 70 200 50 V0 H0Z" fill="#bccfff" />
            <circle cx="70" cy="120" r="26" fill="#ef4444" fill-opacity=".3" stroke="#ef4444" stroke-width="2" />
            <circle cx="140" cy="85" r="22" fill="#f59e0b" fill-opacity=".3" stroke="#f59e0b" stroke-width="2" />
            <circle cx="150" cy="150" r="20" fill="#10b981" fill-opacity=".3" stroke="#10b981" stroke-width="2" />
            <path d="M20 180 L80 40 M60 200 L190 20" stroke="#fff" stroke-width="3" opacity=".7" />
          </svg>
          <div class="absolute top-[38%] left-1/2 -translate-x-1/2 -translate-y-full">
            <span class="absolute -bottom-1 left-1/2 size-6 -translate-x-1/2 animate-pulse-ring rounded-full bg-brote-400" />
            <svg width="48" height="56" viewBox="0 0 44 48" class="relative drop-shadow-lg"><path d="M22 46s16-14.5 16-26A16 16 0 0 0 6 20c0 11.5 16 26 16 26z" fill="#10231b" /><circle cx="22" cy="20" r="7" fill="#c2ee5c" /></svg>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Texto + acciones -->
    <div class="mx-auto w-full max-w-md px-6 pb-8">
      <div class="flex items-center gap-1.5" role="progressbar" :aria-valuenow="paso" aria-valuemin="1" aria-valuemax="3" :aria-label="$t('onboarding.paso', { n: paso })">
        <span v-for="n in 3" :key="n" class="h-1.5 rounded-full transition-all duration-500" :class="n === paso ? 'w-8 bg-brote-400' : n < paso ? 'w-4 bg-brote-400/50' : 'w-4 bg-white/20'" />
      </div>
      <Transition mode="out-in" enter-from-class="opacity-0 translate-y-3" leave-to-class="opacity-0 -translate-y-2" enter-active-class="transition duration-400" leave-active-class="transition duration-150">
        <div :key="paso" class="mt-5">
          <h1 class="font-display text-[34px] leading-[1.05] font-extrabold tracking-tight text-balance">{{ $t(`${claves}.titulo`) }}</h1>
          <p class="mt-3 text-[16px] leading-relaxed text-white/75">{{ $t(`${claves}.texto`) }}</p>
        </div>
      </Transition>

      <div v-if="paso < 3" class="mt-8 flex items-center gap-3">
        <button v-if="paso > 1" type="button" :aria-label="$t('acciones.atras')" class="grid size-14 shrink-0 place-items-center rounded-2xl bg-white/10 ring-1 ring-white/15 transition hover:bg-white/20" @click="paso--">
          <ArrowLeft class="size-5" aria-hidden="true" />
        </button>
        <button v-else type="button" class="min-h-14 px-2 text-sm font-semibold text-white/70 hover:text-white" @click="omitir">{{ $t('acciones.omitir') }}</button>
        <BaseButton variante="acento" class="flex-1" :icono-derecha="ArrowRight" @click="paso++">{{ $t('acciones.siguiente') }}</BaseButton>
      </div>

      <div v-else class="mt-8 space-y-3">
        <BaseButton variante="acento" bloque :icono="Crosshair" :cargando="store.ubicando" @click="usarUbicacion">{{ $t('acciones.usarUbicacion') }}</BaseButton>
        <BaseButton variante="vidrio" bloque :icono="Map" @click="elegirMapa">{{ $t('acciones.elegirMapa') }}</BaseButton>
        <p v-if="errorUbicacion" role="alert" class="rounded-2xl bg-red-500/90 px-4 py-3 text-center text-sm font-medium">{{ $t(`mapa.aviso.${errorUbicacion}`) }}</p>
        <button type="button" class="mx-auto block min-h-11 text-sm font-semibold text-white/60 hover:text-white" @click="paso--">{{ $t('acciones.atras') }}</button>
      </div>
    </div>
  </section>
</template>
