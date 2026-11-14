<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { estado, irA, analizar, fechaHoy } from '../estado'
import { permanentes, MESES, nombreFase } from '../data/catalogo'
import { accionCultivoPermanente } from '../motor/riesgo'
import { t } from '../i18n'
import Icono from '../componentes/Icono.vue'
import Encabezado from '../componentes/Encabezado.vue'
import { preguntar } from '../componentes/asistente'

onMounted(() => { if (!estado.datos && !estado.cargando) analizar() })

const cambiarMes = ref(false)
const indicadorAbierto = ref<string | null>(null)
const nivelTxt = computed(() => ({ alto: t('alto'), medio: t('medio'), bajo: t('bajo') })[estado.ind?.nivel ?? 'bajo'])

const accion = computed(() => {
  if (!estado.ind) return null
  if (estado.modo === 'permanente') return accionCultivoPermanente(estado.permanente, fechaHoy.getMonth(), estado.ind)
  return estado.accion
})
const iconoAccion = computed(() => ({ ESPERAR: 'reloj', SEMBRAR: 'semilla', PROTEGER: 'escudo', REGAR: 'gota', COSECHAR: 'hoja' })[accion.value?.tipo ?? 'SEMBRAR'])
const mejor = computed(() => estado.rotaciones[0])
const preguntas = computed(() => estado.modo === 'permanente'
  ? [`¿Qué riesgo tiene mi ${estado.permanente.toLowerCase()} este mes?`, '¿Cuándo debo regar más?', '¿Viene El Niño costero?']
  : ['¿Por qué no me conviene sembrar arroz?', '¿Qué rotación tiene menos riesgo?', '¿Cuál es el mes más riesgoso de mi campaña?'])

const indicadores = computed(() => {
  const i = estado.ind
  if (!i) return []
  const fuente = i.fuente === 'Ejemplo' ? 'Ejemplo' : 'NASA POWER'
  return [
    { k: 'humedad', ico: 'gota', titulo: 'Humedad del suelo', valor: i.humedadPct === null ? 's/d' : `${i.humedadPct > 0 ? '+' : ''}${i.humedadPct} %`, mal: (i.humedadPct ?? 0) <= -25,
      porque: `Humedad de la capa superficial del suelo en los últimos 30 días frente a la normal de ${MESES[fechaHoy.getMonth()].toLowerCase()} (${fuente}, GWETTOP). SMAP (9 km) la afinará por valle.` },
    { k: 'lluvia', ico: 'ola', titulo: 'Lluvia 30 días', valor: i.lluviaMm30 === null ? 's/d' : `${i.lluviaMm30} mm`, mal: (i.lluviaPct ?? 0) >= 150 || (i.lluviaMm30 !== null && i.lluviaMm30 < 0.5 * i.lluviaNormal30 && i.lluviaNormal30 >= 3),
      porque: `Lo normal para este mes son ${i.lluviaNormal30} mm (${fuente}). GPM IMERG (11 km) distingue la lluvia de cada valle.` },
    { k: 'calor', ico: 'termometro', titulo: 'Calor', valor: i.calorC === null ? 's/d' : `${i.calorC > 0 ? '+' : ''}${i.calorC} °C`, mal: (i.calorC ?? 0) >= 2,
      porque: `Temperatura máxima promedio de los últimos 30 días frente a la normal (${fuente}, T2M_MAX).` },
    { k: 'mar', ico: 'satelite', titulo: 'Mar (El Niño)', valor: i.sstAnomalia === null ? 's/d' : `${i.sstAnomalia > 0 ? '+' : ''}${i.sstAnomalia} °C`, mal: (i.sstAnomalia ?? 0) >= 1.5,
      porque: 'Anomalía de la temperatura del mar frente a la costa (MUR SST, NASA JPL). Si sube más de 1,5 °C es señal de El Niño costero, como en 2017.' },
  ]
})

function compartir() {
  const a = accion.value
  if (!a) return
  const txt = `AllpaShift · ${estado.parcela.nombre}\n${a.tipo}: ${a.titulo}\n${t('motivo')}: ${a.motivo}\n${mejor.value ? `${t('mejorRot')}: ${mejor.value.c1.nombre} - ${mejor.value.c2.nombre} (${mejor.value.puntaje}/100)` : ''}\nhttp://2.29.101.199`
  window.open('https://wa.me/?text=' + encodeURIComponent(txt), '_blank')
}
</script>

<template>
  <section class="pagina">
    <Encabezado />
    <h1>{{ t('queHagoAhora') }}</h1>
    <p class="tenue">{{ t('accion2sem') }}</p>

    <div class="tarjeta eleccion">
      <small class="titulito">{{ t('enQue').toUpperCase() }}</small>
      <div class="opciones">
        <button :class="['opcion', { on: estado.modo === 'sembrar' }]" @click="estado.modo = 'sembrar'">
          <Icono n="brote" :t="22" /> <span><b>{{ t('recomiendame') }}</b><small>{{ t('recomiendameSub') }}</small></span>
        </button>
        <button :class="['opcion', { on: estado.modo === 'permanente' }]" @click="estado.modo = 'permanente'">
          <Icono n="hoja" :t="22" /> <span><b>{{ t('tengoPermanente') }}</b><small>{{ t('tengoPermanenteSub') }}</small></span>
        </button>
      </div>
      <div v-if="estado.modo === 'permanente'" class="permanentes">
        <button v-for="p in permanentes" :key="p" :class="['pill', { on: estado.permanente === p }]" @click="estado.permanente = p">{{ p }}</button>
      </div>
    </div>

    <div v-if="estado.cargando || !estado.ind" class="esqueleto tarjeta-oscura">
      <div class="linea l1"></div><div class="linea l2"></div><div class="linea l3"></div><div class="linea l4"></div>
      <small>{{ t('cargando') }}</small>
    </div>

    <template v-else>
      <div v-if="estado.ind.alerta" class="banner-alerta"><Icono n="alerta" /> <b>{{ t('alerta') }}:</b> {{ estado.ind.alerta }}</div>

      <div class="rejilla-accion">
        <div class="tarjeta-oscura accion">
          <div class="esfera"></div>
          <div class="chips">
            <span class="chip lima">{{ t('accionRec').toUpperCase() }}</span>
            <span :class="['chip', 'oscuro', estado.ind.nivel]"><Icono n="alerta" :t="12" /> {{ t('riesgoClim') }}: {{ nivelTxt }}</span>
          </div>
          <div class="accion-tipo"><span class="accion-ico"><Icono :n="iconoAccion" /></span> {{ accion?.tipo }}</div>
          <h2>{{ accion?.titulo }}</h2>
          <div class="motivo"><b>{{ t('motivo') }}:</b> {{ accion?.motivo }}</div>
          <div class="chips">
            <span class="chip translucido"><Icono n="satelite" :t="12" /> {{ t('dato') }}: {{ estado.ind.fuente }}</span>
            <span v-if="estado.modo === 'sembrar'" class="chip translucido"><Icono n="calendario" :t="12" /> {{ t('siembraPlaneada') }}: {{ MESES[estado.mesSiembra].toLowerCase() }}
              <a href="#" @click.prevent="cambiarMes = !cambiarMes">{{ t('cambiar') }}</a></span>
            <span v-else-if="'fase' in (accion ?? {})" class="chip translucido"><Icono n="calendario" :t="12" /> Fase: {{ nombreFase[(accion as any).fase as 'S'] }}</span>
          </div>
          <div v-if="cambiarMes" class="selector-mes">
            <button v-for="k in 3" :key="k" :class="['pill', { on: estado.mesSiembra === (fechaHoy.getMonth() + k - 1) % 12 }]"
              @click="estado.mesSiembra = (fechaHoy.getMonth() + k - 1) % 12; cambiarMes = false">{{ MESES[(fechaHoy.getMonth() + k - 1) % 12] }}</button>
          </div>
          <button class="btn-whatsapp" @click="compartir"><Icono n="enviar" /> {{ t('whatsapp') }}</button>
        </div>

        <div class="columna">
          <button v-if="mejor && estado.modo === 'sembrar'" class="tarjeta mejor" @click="irA('siembro')">
            <span class="anillo-mini" :style="{ '--p': mejor.puntaje }">{{ mejor.puntaje }}</span>
            <span class="mejor-txt"><small class="verde-txt"><Icono n="brote" :t="12" /> {{ t('mejorRot').toUpperCase() }}</small>
              <b>{{ mejor.c1.nombre }} - {{ mejor.c2.nombre }}</b><span class="tenue">{{ mejor.motivo }}</span></span>
            <Icono n="flecha" />
          </button>
          <div class="tarjeta preguntas">
            <div class="preg-cab"><span class="preg-ico"><Icono n="chispa" /></span><div><b>{{ t('pregunta') }}</b><small class="tenue">{{ t('preguntaSub') }}</small></div></div>
            <button v-for="p in preguntas" :key="p" class="preg" @click="preguntar(p)">{{ p }} <Icono n="diagonal" :t="14" /></button>
          </div>
        </div>
      </div>

      <h3 class="seccion">{{ t('satelites') }}</h3>
      <p class="tenue">{{ t('satelitesSub') }}</p>
      <div class="indicadores">
        <button v-for="i in indicadores" :key="i.k" :class="['tarjeta', 'indicador', { mal: i.mal }]" @click="indicadorAbierto = indicadorAbierto === i.k ? null : i.k">
          <span class="ind-ico"><Icono :n="i.ico" /></span>
          <small>{{ i.titulo }}</small>
          <b>{{ i.valor }}</b>
          <p v-if="indicadorAbierto === i.k" class="tenue">{{ i.porque }}</p>
        </button>
      </div>
    </template>
  </section>
</template>
