<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import { api } from '@/services/api'
import { PARCELA_PIURA, useAppStore } from '@/stores/app'
import type { ResultadoAnio, ResumenValidacion } from '@/types/api'

/**
 * Aciertos y falsas alarmas de TODOS los años desde 2016 (no solo 2017): la misma regla de hoy aplicada a cada año.
 * "Evento" se define con el mismo dato satelital (lluvia feb-abr frente a la normal), para que sea objetivo.
 */
const props = defineProps<{ anio: number }>()
const emit = defineEmits<{ elegir: [anio: number] }>()
const store = useAppStore()

const datos = ref<ResumenValidacion | null>(null)
const estado = ref<'cargando' | 'listo' | 'sin'>('cargando')

async function cargar() {
  estado.value = 'cargando'
  datos.value = await api.getResumenValidacion(PARCELA_PIURA.lat, PARCELA_PIURA.lon, store.idioma)
  estado.value = datos.value ? 'listo' : 'sin'
}
onMounted(cargar)
watch(() => store.idioma, cargar)

const filas = computed(() => [...(datos.value?.filas ?? [])].reverse())   // el año más reciente primero
const c = computed(() => datos.value?.cuenta ?? { acierto: 0, falsa_alarma: 0, no_avisado: 0, correcto: 0, pendiente: 0 })
const TONO: Record<ResultadoAnio, string> = {
  acierto: 'bg-brote-400/20 text-brote-900 dark:text-brote-200',
  falsa_alarma: 'bg-amber-400/20 text-amber-900 dark:text-amber-200',
  no_avisado: 'bg-red-500/15 text-red-800 dark:text-red-200',
  correcto: 'bg-tinta/5 text-stone-600 dark:bg-white/5 dark:text-stone-300',
  pendiente: 'bg-tinta/5 text-stone-500 dark:bg-white/5 dark:text-stone-400',
}
</script>

<template>
  <div class="superficie p-5 sm:p-6">
    <SectionTitle :titulo="$t('resumenValidacion.titulo')" class="mb-1" />
    <p class="text-sm text-stone-600 dark:text-stone-300">{{ $t('resumenValidacion.lead') }}</p>

    <div v-if="estado === 'cargando'" class="mt-4 space-y-2" aria-busy="true">
      <SkeletonBlock class="h-16" />
      <SkeletonBlock class="h-40" />
    </div>
    <p v-else-if="estado === 'sin'" class="mt-4 text-sm text-stone-500 dark:text-stone-400">{{ $t('resumenValidacion.noDisponible') }}</p>

    <template v-else-if="datos">
      <dl class="mt-4 grid grid-cols-2 gap-3">
        <div class="rounded-2xl bg-brote-400/15 p-3">
          <dt class="text-xs font-bold text-stone-600 dark:text-stone-300">{{ $t('resumenValidacion.deteccion') }}</dt>
          <dd class="font-display text-xl font-bold">{{ $t('resumenValidacion.avisoTexto', { a: c.acierto, e: c.acierto + c.no_avisado }) }}</dd>
        </div>
        <div class="rounded-2xl bg-amber-400/15 p-3">
          <dt class="text-xs font-bold text-stone-600 dark:text-stone-300">{{ $t('resumenValidacion.falsas') }}</dt>
          <dd class="font-display text-xl font-bold">{{ $t('resumenValidacion.falsasTexto', { c: c.acierto, f: c.falsa_alarma }) }}</dd>
        </div>
      </dl>
      <p class="mt-3 text-[15px] leading-relaxed text-stone-700 dark:text-stone-300">
        {{ $t('resumenValidacion.resumenFrase', { n: datos.filas.length, e: c.acierto + c.no_avisado, a: c.acierto, t: c.acierto + c.falsa_alarma, c: c.acierto, f: c.falsa_alarma }) }}
      </p>

      <div class="mt-4 overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="text-xs text-stone-500 dark:text-stone-400">
            <tr>
              <th scope="col" class="py-2 pr-2 font-bold">{{ $t('resumenValidacion.anio') }}</th>
              <th scope="col" class="py-2 pr-2 font-bold">{{ $t('resumenValidacion.alerta') }}</th>
              <th scope="col" class="py-2 pr-2 font-bold">{{ $t('resumenValidacion.lluvia') }}</th>
              <th scope="col" class="py-2 font-bold">{{ $t('resumenValidacion.resultado') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="f in filas"
              :key="f.anio"
              class="border-t border-tinta/8 dark:border-white/10"
              :class="f.anio === props.anio && 'bg-tinta/[0.03] dark:bg-white/[0.04]'"
            >
              <td class="py-2 pr-2">
                <button
                  type="button"
                  class="min-h-11 min-w-11 font-bold tabular-nums underline-offset-4 hover:underline"
                  :aria-current="f.anio === props.anio ? 'true' : undefined"
                  @click="emit('elegir', f.anio)"
                >
                  {{ f.anio }}
                </button>
              </td>
              <td class="py-2 pr-2 tabular-nums">{{ f.alertaDrenaje?.fecha ?? $t('resumenValidacion.sinAlerta') }}</td>
              <td class="py-2 pr-2 tabular-nums">{{ f.veces === null ? '—' : $t('resumenValidacion.veces', { v: f.veces.toFixed(1) }) }}</td>
              <td class="py-2">
                <span class="inline-block rounded-full px-2 py-0.5 text-xs font-bold" :class="TONO[f.resultado]">
                  {{ $t(`resumenValidacion.${f.resultado}`) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="mt-3 text-xs leading-snug text-stone-500 dark:text-stone-400">{{ datos.definicionEvento }} GPM IMERG · MUR SST.</p>
    </template>
  </div>
</template>
