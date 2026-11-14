<script setup lang="ts">
import { BarChart3, ChevronRight, ClipboardCheck, Satellite, TrafficCone } from 'lucide-vue-next'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

/**
 * "Cómo funciona": recorrido de 4 pasos conectados (satélite → lo normal → semáforo → qué hacer).
 * Escritorio: horizontal con línea punteada entre pasos. Celular: línea de tiempo vertical.
 * Los pasos 3 y 4 MUESTRAN el semáforo y las acciones en vez de describirlos.
 */
const { tm, rt } = useI18n()

const ESTILO = [
  { icono: Satellite, burbuja: 'bg-nasa-600 text-white', aro: 'ring-nasa-200 dark:ring-nasa-400/30' },
  { icono: BarChart3, burbuja: 'bg-amber-500 text-white', aro: 'ring-amber-200 dark:ring-amber-400/30' },
  { icono: TrafficCone, burbuja: 'bg-red-500 text-white', aro: 'ring-red-200 dark:ring-red-400/30' },
  { icono: ClipboardCheck, burbuja: 'bg-brote-400 text-tinta', aro: 'ring-brote-200 dark:ring-brote-400/30' },
]

const pasos = computed(() =>
  (tm('datos.como') as { titulo: unknown; texto: unknown }[]).map((p, i) => ({
    titulo: rt(p.titulo as never),
    texto: rt(p.texto as never),
    ...ESTILO[i],
  })),
)

const SEMAFORO = [
  { clave: 'riesgo.bajo', clase: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-400/15 dark:text-emerald-300', punto: 'bg-emerald-500' },
  { clave: 'riesgo.medio', clase: 'bg-amber-100 text-amber-800 dark:bg-amber-400/15 dark:text-amber-300', punto: 'bg-amber-500' },
  { clave: 'riesgo.alto', clase: 'bg-red-100 text-red-800 dark:bg-red-400/15 dark:text-red-300', punto: 'bg-red-500' },
]
const ACCIONES = ['accion.sembrar', 'accion.esperar', 'accion.regar', 'accion.proteger', 'accion.drenaje']
</script>

<template>
  <section class="superficie p-5 sm:p-7" :aria-label="$t('datos.comoTitulo')">
    <h2 class="font-display text-2xl font-bold tracking-tight">{{ $t('datos.comoTitulo') }}</h2>
    <p class="mt-1 text-[15px] text-stone-600 dark:text-stone-400">{{ $t('datos.comoSubtitulo') }}</p>

    <ol class="mt-6 grid grid-cols-1 gap-0 lg:grid-cols-4">
      <li v-for="(p, i) in pasos" :key="i" class="relative pb-7 pl-[72px] last:pb-0 lg:px-4 lg:pb-0 lg:pl-4 lg:text-center">
        <!-- Conector: vertical en celular, horizontal en escritorio -->
        <template v-if="i < pasos.length - 1">
          <span class="absolute top-16 bottom-0 left-7 border-l-2 border-dashed border-tinta/15 lg:hidden dark:border-white/15" aria-hidden="true" />
          <span class="absolute top-7 right-[calc(36px-50%)] left-[calc(50%+36px)] hidden border-t-2 border-dashed border-tinta/15 lg:block dark:border-white/15" aria-hidden="true" />
          <ChevronRight class="absolute top-[18px] -right-[11px] hidden size-5 text-tinta/30 lg:block dark:text-white/30" aria-hidden="true" />
        </template>

        <!-- Ícono con número -->
        <div class="absolute top-0 left-0 lg:relative lg:mx-auto lg:w-fit">
          <span class="grid size-14 place-items-center rounded-full ring-8" :class="[p.burbuja, p.aro]">
            <component :is="p.icono" class="size-6" :stroke-width="2.2" aria-hidden="true" />
          </span>
          <span class="absolute -top-1 -right-1 grid size-6 place-items-center rounded-full bg-tinta text-xs font-bold text-white ring-2 ring-white dark:bg-white dark:text-tinta dark:ring-noche-2">
            {{ i + 1 }}
          </span>
        </div>

        <div class="lg:mt-5">
          <h3 class="font-display text-[17px] leading-snug font-bold">{{ p.titulo }}</h3>
          <p class="mt-1 text-[15px] leading-relaxed text-stone-600 dark:text-stone-300">{{ p.texto }}</p>

          <!-- Paso 3: el semáforo -->
          <ul v-if="i === 2" class="mt-3 flex flex-wrap gap-1.5 lg:justify-center">
            <li v-for="s in SEMAFORO" :key="s.clave" class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold" :class="s.clase">
              <span class="size-2 rounded-full" :class="s.punto" aria-hidden="true" />{{ $t(s.clave) }}
            </li>
          </ul>
          <!-- Paso 4: las acciones posibles -->
          <ul v-if="i === 3" class="mt-3 flex flex-wrap gap-1.5 lg:justify-center">
            <li v-for="a in ACCIONES" :key="a" class="rounded-full bg-brote-400/20 px-2.5 py-1 text-xs font-semibold text-agro-800 dark:text-brote-300">
              {{ $t(a) }}
            </li>
          </ul>
        </div>
      </li>
    </ol>
  </section>
</template>
