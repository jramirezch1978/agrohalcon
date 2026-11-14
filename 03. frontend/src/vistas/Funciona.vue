<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { estado } from '../estado'
import { serieMensual } from '../motor/nasa'
import { MES_CORTO } from '../data/catalogo'
import Icono from '../componentes/Icono.vue'

echarts.use([BarChart, LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

// Lluvia de marzo por valle con GPM IMERG (mm/mes), medida el 2026-11-14 (doc 24)
const valles = [
  { v: 'Sechura', a: 61, b: 552 }, { v: 'Catacaos (Bajo Piura)', a: 68, b: 540 }, { v: 'Castilla (Medio Piura)', a: 77, b: 580 },
  { v: 'Sullana (Chira)', a: 99, b: 542 }, { v: 'Tambogrande (San Lorenzo)', a: 138, b: 590 }, { v: 'Chulucanas (Alto Piura)', a: 152, b: 577 },
  { v: 'Huancabamba (sierra)', a: 160, b: 320 },
]
const div = ref<HTMLDivElement>()
const estadoSerie = ref<'cargando' | 'ok' | 'error'>('cargando')
const alertaEnero = ref('')
let chart: echarts.ECharts | undefined

async function cargar() {
  estadoSerie.value = 'cargando'
  try {
    const s = await serieMensual(estado.parcela.lat, estado.parcela.lon, 2016, 2017)
    const a16 = s.filter((x) => x.mes.startsWith('2016')).map((x) => +(x.lluviaMmDia * 30).toFixed(0))
    const a17 = s.filter((x) => x.mes.startsWith('2017')).map((x) => +(x.lluviaMmDia * 30).toFixed(0))
    const h17 = s.filter((x) => x.mes.startsWith('2017')).map((x) => +x.humedadRaiz.toFixed(2))
    const ene = a17[0], eneN = Math.max(a16[0], 1)
    alertaEnero.value = ene > 1.5 * eneN
      ? `En enero de 2017 la lluvia ya era ${(ene / eneN).toFixed(1)} veces la de 2016. AllpaShift habría marcado riesgo ALTO de lluvia y recomendado PROTEGER: drenes, cosechar antes y no sembrar arroz en zonas inundables, unas 6 semanas antes del pico de marzo.`
      : 'En esta coordenada la señal de enero fue débil; la alerta se activa en febrero, cuando la lluvia supera ampliamente lo normal.'
    estadoSerie.value = 'ok'
    await nextTick()
    chart ??= echarts.init(div.value!)
    const oscuro = estado.tema === 'oscuro'
    const txt = oscuro ? '#e7efe4' : '#1f2a24'
    chart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0, textStyle: { color: txt } },
      grid: { left: 50, right: 50, top: 30, bottom: 70 },
      xAxis: { type: 'category', data: MES_CORTO, axisLabel: { color: txt } },
      yAxis: [{ type: 'value', name: 'mm/mes', nameTextStyle: { color: txt }, axisLabel: { color: txt }, splitLine: { lineStyle: { color: oscuro ? '#2a3a30' : '#e5ebe2' } } },
        { type: 'value', name: 'humedad raíz', min: 0, max: 1, nameTextStyle: { color: txt }, axisLabel: { color: txt }, splitLine: { show: false } }],
      series: [
        { name: 'Lluvia 2016 (normal)', type: 'bar', data: a16, itemStyle: { color: '#94a3b8', borderRadius: [4, 4, 0, 0] } },
        { name: 'Lluvia 2017 (Niño costero)', type: 'bar', data: a17, itemStyle: { color: '#ef4444', borderRadius: [4, 4, 0, 0] } },
        { name: 'Humedad de raíz 2017', type: 'line', yAxisIndex: 1, data: h17, smooth: true, itemStyle: { color: '#22c55e' } },
      ],
    })
  } catch { estadoSerie.value = 'error' }
}
onMounted(cargar)
watch(() => estado.tema, () => { chart?.dispose(); chart = undefined; cargar() })
onBeforeUnmount(() => chart?.dispose())
</script>

<template>
  <section class="pagina">
    <h1>¿Funciona? La máquina del tiempo</h1>
    <p class="tenue">Qué habría dicho AllpaShift antes del <b>Niño Costero de 2017</b>, el evento que los índices globales (ONI) marcaron como «neutral» y que arrasó los valles de Piura.</p>

    <div class="tarjeta">
      <h3><Icono n="satelite" /> Lluvia 2016 frente a 2017 en tu parcela · NASA POWER</h3>
      <small class="tenue">{{ estado.parcela.nombre }} ({{ estado.parcela.lat.toFixed(2) }}, {{ estado.parcela.lon.toFixed(2) }})</small>
      <div v-if="estadoSerie === 'cargando'" class="esqueleto claro"><div class="linea l1"></div><div class="linea l2"></div></div>
      <p v-else-if="estadoSerie === 'error'" class="tenue">NASA POWER no respondió. Intenta de nuevo en unos segundos.</p>
      <div v-show="estadoSerie === 'ok'" ref="div" class="grafico alto"></div>
      <div v-if="estadoSerie === 'ok'" class="banner-info"><Icono n="reloj" /> {{ alertaEnero }}</div>
    </div>

    <div class="tarjeta">
      <h3><Icono n="ola" /> Lluvia de marzo por valle · GPM IMERG (0,1°)</h3>
      <p class="tenue">IMERG distingue valles que en NASA POWER (0,5°) salen iguales. El Niño Costero golpeó más al Bajo Piura y Sechura.</p>
      <table class="tabla">
        <thead><tr><th>Valle</th><th>Marzo 2016</th><th>Marzo 2017</th><th>Veces más</th></tr></thead>
        <tbody>
          <tr v-for="x in valles" :key="x.v"><td>{{ x.v }}</td><td>{{ x.a }} mm</td><td><b>{{ x.b }} mm</b></td>
            <td><span :class="['chip', x.b / x.a >= 5 ? 'alto' : 'medio']">×{{ (x.b / x.a).toFixed(1) }}</span></td></tr>
        </tbody>
      </table>
      <small class="tenue">Fuente: GPM IMERG Final mensual V07 (NASA GES DISC), DOI 10.5067/GPM/IMERG/3B-MONTH/07.</small>
    </div>
  </section>
</template>
