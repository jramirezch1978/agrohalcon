<script setup lang="ts">
import Icono from '../componentes/Icono.vue'
const pasos = [
  { ico: 'mapa', t: '1. Marca tu parcela', d: 'En «Mapa», toca el punto, busca el lugar o usa tu ubicación. Los círculos verdes son los valles agrícolas del norte.' },
  { ico: 'satelite', t: '2. Leemos los satélites', d: 'AllpaShift consulta los datos de la NASA de ese punto: lluvia, humedad del suelo, calor y temperatura del mar.' },
  { ico: 'sol', t: '3. ¿Qué hago?', d: 'La acción de las próximas 2 semanas, con el motivo y el dato NASA que la respalda.' },
  { ico: 'brote', t: '4. ¿Qué siembro?', d: 'Tres rotaciones con puntaje de 0 a 100 y la barra de riesgo de cada mes de la campaña.' },
]
const datos = [
  ['NASA POWER', 'Clima histórico y reciente (lluvia, temperatura, humedad del suelo)', '0,5° (~55 km)'],
  ['GPM IMERG', 'Lluvia por valle', '0,1° (~11 km)'],
  ['SMAP', 'Humedad del suelo', '9 km'],
  ['MODIS NDVI', 'Vigor de la vegetación', '250 m'],
  ['MUR SST', 'Temperatura del mar (El Niño costero)', '1 km'],
  ['SRTM', 'Relieve y pendiente', '30 m'],
]
</script>

<template>
  <section class="pagina">
    <h1>Ayuda</h1>
    <p class="tenue"><b>AllpaShift</b> (<i>allpa</i> = tierra en quechua) te dice qué sembrar, cuándo y qué hacer esta quincena según el riesgo climático que ven los satélites de la NASA.</p>
    <div class="pasos">
      <div v-for="p in pasos" :key="p.t" class="tarjeta paso"><span class="ind-ico"><Icono :n="p.ico" /></span><b>{{ p.t }}</b><p class="tenue">{{ p.d }}</p></div>
    </div>
    <div class="tarjeta">
      <h3>Datos de la NASA que usamos</h3>
      <table class="tabla"><thead><tr><th>Dataset</th><th>Para qué</th><th>Resolución</th></tr></thead>
        <tbody><tr v-for="d in datos" :key="d[0]"><td><b>{{ d[0] }}</b></td><td>{{ d[1] }}</td><td>{{ d[2] }}</td></tr></tbody></table>
    </div>
    <div class="aviso"><Icono n="info" :t="16" /> AllpaShift es una herramienta de apoyo: no reemplaza al técnico agrario. Los calendarios y umbrales son preliminares y se validan con MIDAGRI y FAO-56. Proyecto del equipo Halcón Dorado para NASA Space Apps Challenge Piura 2026.</div>
  </section>
</template>
