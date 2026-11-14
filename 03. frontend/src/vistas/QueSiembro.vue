<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { estado, analizar, fechaHoy } from '../estado'
import { MESES, MES_CORTO } from '../data/catalogo'
import type { MesCampania, Rotacion } from '../motor/riesgo'
import { t } from '../i18n'
import Icono from '../componentes/Icono.vue'
import Encabezado from '../componentes/Encabezado.vue'

echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

onMounted(() => { if (!estado.datos && !estado.cargando) analizar() })

const opcionesMes = computed(() => [0, 1, 2].map((k) => ({ mes: (fechaHoy.getMonth() + k) % 12, sub: [t('esteMes'), t('proximo'), t('en2')][k] })))
const abierto = ref<string | null>(null)
const mesSel = ref<Record<string, MesCampania | null>>({})
const clave = (r: Rotacion) => r.c1.nombre + '>' + r.c2.nombre
const nivelTxt = (n: string) => ({ alto: t('alto'), medio: t('medio'), bajo: t('bajo') })[n as 'alto']
const gotas = (a: string) => ({ baja: 1, media: 2, alta: 3 })[a as 'baja']
const colorAnillo = (p: number) => (p >= 70 ? '#22c55e' : p >= 50 ? '#f59e0b' : '#ef4444')

// Puntaje animado de 0 a N
const mostrado = ref<Record<string, number>>({})
function animar() {
  const ini = performance.now()
  const objetivo = Object.fromEntries(estado.rotaciones.map((r) => [clave(r), r.puntaje]))
  const paso = (ahora: number) => {
    const f = Math.min(1, (ahora - ini) / 900)
    const e = 1 - (1 - f) ** 3
    mostrado.value = Object.fromEntries(Object.entries(objetivo).map(([k, v]) => [k, Math.round(v * e)]))
    if (f < 1) requestAnimationFrame(paso)
  }
  requestAnimationFrame(paso)
}
watch(() => estado.rotaciones, () => { animar(); nextTick(dibujar) }, { immediate: true })

const grafico = ref<HTMLDivElement>()
let chart: echarts.ECharts | undefined
function dibujar() {
  if (!grafico.value || !estado.rotaciones.length) return
  chart ??= echarts.init(grafico.value)
  const oscuro = estado.tema === 'oscuro'
  chart.setOption({
    grid: { left: 140, right: 40, top: 10, bottom: 24 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'value', max: 100, axisLabel: { color: oscuro ? '#cbd5c8' : '#4b5a50' }, splitLine: { lineStyle: { color: oscuro ? '#2a3a30' : '#e5ebe2' } } },
    yAxis: { type: 'category', inverse: true, data: estado.rotaciones.map((r) => `${r.c1.nombre} → ${r.c2.nombre}`), axisLabel: { color: oscuro ? '#e7efe4' : '#1f2a24' } },
    series: [{ type: 'bar', barWidth: 18, data: estado.rotaciones.map((r) => ({ value: r.puntaje, itemStyle: { color: colorAnillo(r.puntaje), borderRadius: [0, 6, 6, 0] } })), label: { show: true, position: 'right', color: oscuro ? '#fff' : '#1f2a24' } }],
  })
}
const redim = () => chart?.resize()
onMounted(() => window.addEventListener('resize', redim))
onBeforeUnmount(() => { window.removeEventListener('resize', redim); chart?.dispose() })
watch(() => estado.tema, () => { chart?.dispose(); chart = undefined; nextTick(dibujar) })
</script>

<template>
  <section class="pagina">
    <Encabezado />
    <h1>{{ t('queConviene') }}</h1>
    <p class="tenue">{{ t('tocaTarjeta') }}</p>

    <div class="fila-filtros">
      <div class="tarjeta eleccion">
        <small class="titulito">{{ t('enQue').toUpperCase() }}</small>
        <div class="opciones">
          <button :class="['opcion', { on: estado.modo === 'sembrar' }]" @click="estado.modo = 'sembrar'">
            <Icono n="brote" :t="22" /> <span><b>{{ t('recomiendame') }}</b><small>{{ t('recomiendameSub') }}</small></span>
          </button>
          <a class="opcion" href="#/campana" @click="estado.modo = 'permanente'">
            <Icono n="hoja" :t="22" /> <span><b>{{ t('tengoPermanente') }}</b><small>{{ t('tengoPermanenteSub') }}</small></span>
          </a>
        </div>
      </div>
      <div class="tarjeta eleccion">
        <small class="titulito"><Icono n="calendario" :t="12" /> {{ t('cuando').toUpperCase() }}</small>
        <div class="meses">
          <button v-for="o in opcionesMes" :key="o.mes" :class="['mes-opc', { on: estado.mesSiembra === o.mes }]" @click="estado.mesSiembra = o.mes">
            <b>{{ MESES[o.mes] }}</b><small>{{ o.sub }}</small>
          </button>
        </div>
      </div>
    </div>

    <div class="aviso"><Icono n="info" :t="16" /> {{ t('aviso') }}</div>

    <div v-if="estado.cargando || !estado.rotaciones.length" class="esqueleto tarjeta-oscura"><div class="linea l1"></div><div class="linea l2"></div><small>{{ t('cargando') }}</small></div>

    <div v-else class="rotaciones">
      <article v-for="(r, i) in estado.rotaciones" :key="clave(r)" :class="['tarjeta', 'rot', { recomendada: i === 0 }]">
        <span v-if="i === 0" class="cinta"><Icono n="escudo" :t="12" /> {{ t('recomendada').toUpperCase() }}</span>
        <div class="anillo" :style="{ '--p': mostrado[clave(r)] ?? 0, '--c': colorAnillo(r.puntaje) }">
          <b>{{ mostrado[clave(r)] ?? 0 }}</b><small>{{ t('de100') }}</small>
        </div>
        <h3>{{ r.c1.nombre }} → {{ r.c2.nombre }}</h3>
        <span :class="['chip', r.nivel]"><Icono :n="r.nivel === 'alto' ? 'alerta' : r.nivel === 'medio' ? 'info' : 'check'" :t="12" /> {{ t('riesgo') }} {{ nivelTxt(r.nivel) }}</span>
        <span class="chip agua"><span v-for="g in 3" :key="g" :class="{ apagada: g > gotas(r.agua) }">💧</span> {{ t('usoAgua') }}: {{ r.agua }}</span>
        <p>{{ r.motivo }}</p>
        <button class="enlace" @click="abierto = abierto === clave(r) ? null : clave(r)">{{ t('porQue') }} <Icono n="flecha" :t="12" /></button>
        <ul v-if="abierto === clave(r)" class="porque"><li v-for="p in r.porque" :key="p">{{ p }}</li></ul>

        <div class="campania">
          <small class="titulito">{{ t('perspectiva').toUpperCase() }}</small>
          <p class="mini"><b>{{ t('siembra') }}:</b> {{ MESES[r.siembra].toLowerCase() }} · <b>{{ t('cosecha') }}:</b> {{ MESES[r.cosecha].toLowerCase() }}<br /><b>{{ t('duracion') }}:</b> {{ r.duracion }} {{ t('meses') }}</p>
          <div class="barra-meses">
            <button v-for="(m, k) in r.campania" :key="k" :class="['mes-celda', m.color, { sel: mesSel[clave(r)] === m, peor: r.mesMasRiesgoso === m }]"
              :title="`${MESES[m.mes]} ${m.anio}: ${m.motivo}`" @click="mesSel[clave(r)] = mesSel[clave(r)] === m ? null : m">{{ MES_CORTO[m.mes] }}</button>
          </div>
          <span v-if="r.mesMasRiesgoso" class="chip peor-chip"><Icono n="bandera" :t="12" /> {{ t('masRiesgoso') }}: {{ MESES[r.mesMasRiesgoso.mes] }}</span>
          <small v-else class="tenue">{{ t('tocaMes') }}</small>
          <div v-if="mesSel[clave(r)]" class="detalle-mes">
            <b>{{ MESES[mesSel[clave(r)]!.mes] }} de {{ mesSel[clave(r)]!.anio }}:</b> {{ mesSel[clave(r)]!.motivo }}
            <small><Icono n="satelite" :t="11" /> {{ t('fuente') }}: {{ estado.ind?.fuente === 'Ejemplo' ? 'Ejemplo' : 'NASA POWER (normal mensual)' }}</small>
          </div>
        </div>
      </article>
    </div>

    <div v-show="estado.rotaciones.length" class="tarjeta comparacion">
      <h3>{{ t('comparacion') }}</h3>
      <div ref="grafico" class="grafico"></div>
    </div>
  </section>
</template>
