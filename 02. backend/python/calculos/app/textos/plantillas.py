"""Plantillas de texto es/en (sin IA). Cada frase cita el número que la decidió."""
from __future__ import annotations

Lang = str  # "es" | "en"

UNIDADES = {
    "es": {"lluvia": "mm/día", "humedadSuelo": "fracción 0-1", "calor": "°C", "elNino": "°C anomalía"},
    "en": {"lluvia": "mm/day", "humedadSuelo": "fraction 0-1", "calor": "°C", "elNino": "°C anomaly"},
}

TEXTOS: dict[Lang, dict[str, str]] = {
    "es": {
        "lluvia_deficit": "Lluvia {abs:.0f} % bajo lo normal en los últimos {dias} días ({valor:.2f} vs {normal:.2f} mm/día).",
        "lluvia_exceso": "Lluvia {abs:.0f} % sobre lo normal en los últimos {dias} días ({valor:.2f} vs {normal:.2f} mm/día).",
        "lluvia_veces": "Lluvia {veces:.0f} veces lo normal en los últimos {dias} días ({valor:.2f} vs {normal:.2f} mm/día).",
        "lluvia_seca": "Estación seca: casi no llueve y es lo normal ({valor:.2f} vs {normal:.2f} mm/día).",
        "humedad_deficit": "Humedad del suelo {abs:.0f} % bajo lo normal en los últimos {dias} días.",
        "humedad_exceso": "Humedad del suelo {abs:.0f} % sobre lo normal (sin riesgo de sequía).",
        "aviso_smap_sin": "SMAP no tiene datos recientes para este punto: se usa NASA POWER (modelo, celda de ~50 km).",
        "vegetacion_deficit": "Vegetación {abs:.0f} % menos verde que lo normal para esta época (NDVI {valor:.2f}).",
        "vegetacion_exceso": "Vegetación {abs:.0f} % más verde que lo normal para esta época (NDVI {valor:.2f}).",
        "calor": "Temperatura máxima {signo}{diff:.1f} °C frente a lo normal ({valor:.1f} vs {normal:.1f} °C).",
        "elnino": "Mar frente a Perú y Ecuador (Niño 1+2): {signo}{valor:.1f} °C frente a lo normal (semana del {semana}).",
        "elnino_sin_datos": "Sin dato de temperatura del mar (falta correr scripts/descargar_mur_sst.py).",
        "aviso_imerg_viejo": "Dato satelital de lluvia atrasado: el último es del {fecha}.",
        "aviso_imerg_sin": "Sin lluvia satelital reciente (último dato GPM IMERG: {fecha}). Se muestra NASA POWER, que es un modelo y puede exagerar la lluvia en Piura.",
    },
    "en": {
        "lluvia_deficit": "Rainfall {abs:.0f}% below normal over the last {dias} days ({valor:.2f} vs {normal:.2f} mm/day).",
        "lluvia_exceso": "Rainfall {abs:.0f}% above normal over the last {dias} days ({valor:.2f} vs {normal:.2f} mm/day).",
        "lluvia_veces": "Rainfall {veces:.0f}× normal over the last {dias} days ({valor:.2f} vs {normal:.2f} mm/day).",
        "lluvia_seca": "Dry season: almost no rain, which is normal ({valor:.2f} vs {normal:.2f} mm/day).",
        "humedad_deficit": "Soil moisture {abs:.0f}% below normal over the last {dias} days.",
        "humedad_exceso": "Soil moisture {abs:.0f}% above normal (no drought risk).",
        "aviso_smap_sin": "No recent SMAP data for this point: NASA POWER is used (model, ~50 km cell).",
        "vegetacion_deficit": "Vegetation {abs:.0f}% less green than normal for this time of year (NDVI {valor:.2f}).",
        "vegetacion_exceso": "Vegetation {abs:.0f}% greener than normal for this time of year (NDVI {valor:.2f}).",
        "calor": "Maximum temperature {signo}{diff:.1f} °C vs normal ({valor:.1f} vs {normal:.1f} °C).",
        "elnino": "Sea off Peru and Ecuador (Niño 1+2) {signo}{valor:.1f} °C vs normal (week of {semana}).",
        "elnino_sin_datos": "No sea surface temperature data (run scripts/descargar_mur_sst.py).",
        "aviso_imerg_viejo": "Satellite rainfall data is behind: the latest is from {fecha}.",
        "aviso_imerg_sin": "No recent satellite rainfall (last GPM IMERG value: {fecha}). Showing NASA POWER, a model that may overstate rain in Piura.",
    },
}


def texto(lang: Lang, clave: str, **kw) -> str:
    return TEXTOS.get(lang, TEXTOS["es"])[clave].format(**kw)


def signo(x: float) -> str:
    return "+" if x >= 0 else "−"


# ---------- Fase 2: campaña, rotaciones, qué hacer, permanentes y validación ----------

MESES = {
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
           "noviembre", "diciembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"],
}

TEXTOS["es"].update({
    # Campaña (motivo de cada mes)
    "c_calor": "La máxima normal de {mes} ({t:.1f} °C) supera lo que tolera el {cultivo} ({lim:.0f} °C).",
    "c_frio": "La mínima normal de {mes} ({t:.1f} °C) queda bajo lo que tolera el {cultivo} ({lim:.0f} °C).",
    "c_exceso": "En {mes} llueven normalmente {mm:.0f} mm: {veces:.1f} veces lo que necesita el {cultivo}.",
    "c_deficit": "En {mes} llueven normalmente {mm:.0f} mm de los ~{nec:.0f} que necesita el {cultivo}: depende del riego.",
    "c_ok": "El clima normal de {mes} está dentro de lo que tolera el {cultivo}.",
    "c_nino": "El Niño costero ({signo}{anom:.1f} °C, MUR SST) sube un nivel el riesgo de lluvias.",
    "c_exceso_nino": "En {mes} llueven normalmente {mm:.0f} mm, pero El Niño costero ({signo}{anom:.1f} °C, "
                     "MUR SST) sube el riesgo de lluvias extremas.",
    "c_sin_nino": "Sin señal de El Niño disponible.",
    # Rotaciones
    "r_ok": "Sin descuentos: el clima de la campaña le favorece.",
    "r_pierde": "Pierde {p} puntos, sobre todo por {razon}.",
    "r_agua": "su alto uso de agua con {ind} en déficit",
    "r_temp": "{n} mes(es) fuera de su rango de temperatura",
    "r_alto": "{n} mes(es) de la campaña con riesgo alto",
    "r_siembra": "sembrar {cultivo} fuera de sus meses recomendados",
    "r_tradicional": " Es la rotación tradicional de la zona, para comparar.",
    "ind_lluvia": "la lluvia", "ind_humedadSuelo": "la humedad del suelo",
    # Qué hacer esta quincena
    "q_drenaje": "Prepara los drenajes y no siembres en zonas bajas que se inundan",
    "q_drenaje_m": "El mar frente a Perú y Ecuador está {signo}{anom:.1f} °C sobre lo normal (semana del {semana}): "
                   "señal de El Niño costero y de lluvias extremas.",
    "q_esperar_seco": "Espera para sembrar: el suelo está seco",
    "q_regar": "Riega tu {cultivo}: el suelo está seco",
    "q_seco_m": "{ind} está {abs:.0f} % por debajo de lo normal.",
    "q_proteger": "Protege el cultivo del calor: riega temprano y evita trabajar en las horas de más sol",
    "q_proteger_m": "La temperatura máxima está {signo}{dif:.1f} °C sobre lo normal ({valor:.1f} °C).",
    "q_sembrar": "Siembra {rotacion}: es la rotación con mejor puntaje ({p}/100)",
    "q_sembrar_m": "Ningún indicador está en nivel alto y {mes} es mes de siembra de {cultivo}.",
    "q_esperar_mes": "Espera a {mes} para sembrar {rotacion}",
    "q_esperar_mes_m": "{mes_hoy} no es mes de siembra recomendado de {cultivo}; ningún indicador está en nivel alto.",
    "q_plan": "Sigue el manejo normal de {etapa}",
    "q_plan_m": "Ningún indicador está en nivel alto.",
    # Permanentes
    "p_motivo": "{etapa} en {mes}: {razon}",
    # Validación
    "v_evento_2017": "El Niño costero 2017",
    "v_accion_mur": "Vigila el mar: prepara drenajes y no siembres en zonas que se inundan",
    "v_accion_drenaje": "Prepara los drenajes y no siembres en zonas bajas que se inundan",
    "v_motivo_mur": "El mar en Niño 1+2 llegó a {signo}{anom:.2f} °C sobre lo normal (semana del {semana}).",
    "v_accion_lluvia": "Prepara drenajes: la lluvia ya está muy por encima de lo normal",
    "v_motivo_lluvia": "La lluvia de {mes} fue {veces:.1f} veces lo normal.",
    "v_nota_lluvia": "Alerta calculada solo con lluvia; con MUR SST sería más anticipada",
    "v_resumen": "En {mes} llovió {veces:.1f} veces lo normal ({fuente}). AgroShift habría alertado el {fecha}, "
                 "{semanas} semanas antes.",
    "v_resumen_sin_alerta": "Lluvia máxima en {mes} ({veces:.1f} veces lo normal, {fuente}). Con las reglas actuales "
                            "no se habría disparado una alerta entre diciembre y abril.",
    "v_sin_alerta": "Sin alerta: sigue tu calendario de siembra",
    "v_realidad_2017": "Entre enero y abril de 2017 las lluvias de El Niño costero causaron inundaciones y huaicos "
                       "en la costa norte del Perú. En Piura, el río Piura se desbordó el 27 de marzo e inundó la "
                       "ciudad y el Bajo Piura.",
})

TEXTOS["en"].update({
    "c_calor": "The normal maximum in {mes} ({t:.1f} °C) is above what {cultivo} tolerates ({lim:.0f} °C).",
    "c_frio": "The normal minimum in {mes} ({t:.1f} °C) is below what {cultivo} tolerates ({lim:.0f} °C).",
    "c_exceso": "{mes} normally gets {mm:.0f} mm of rain: {veces:.1f} times what {cultivo} needs.",
    "c_deficit": "{mes} normally gets {mm:.0f} mm of the ~{nec:.0f} mm {cultivo} needs: it depends on irrigation.",
    "c_ok": "The normal climate in {mes} is within what {cultivo} tolerates.",
    "c_nino": "Coastal El Niño ({signo}{anom:.1f} °C, MUR SST) raises the rain risk by one level.",
    "c_exceso_nino": "{mes} normally gets {mm:.0f} mm, but coastal El Niño ({signo}{anom:.1f} °C, MUR SST) "
                     "raises the risk of extreme rain.",
    "c_sin_nino": "No El Niño signal available.",
    "r_ok": "No deductions: the season's climate suits it.",
    "r_pierde": "Loses {p} points, mainly because of {razon}.",
    "r_agua": "its high water use with {ind} in deficit",
    "r_temp": "{n} month(s) outside its temperature range",
    "r_alto": "{n} month(s) of the season at high risk",
    "r_siembra": "planting {cultivo} outside its recommended months",
    "r_tradicional": " It is the traditional rotation of the area, for comparison.",
    "ind_lluvia": "rainfall", "ind_humedadSuelo": "soil moisture",
    "q_drenaje": "Prepare drainage and don't plant in low, flood-prone areas",
    "q_drenaje_m": "The sea off Peru and Ecuador is {signo}{anom:.1f} °C above normal (week of {semana}): "
                   "a sign of coastal El Niño and extreme rain.",
    "q_esperar_seco": "Wait to plant: the soil is dry",
    "q_regar": "Irrigate your {cultivo}: the soil is dry",
    "q_seco_m": "{ind} is {abs:.0f}% below normal.",
    "q_proteger": "Protect the crop from heat: irrigate early and avoid working in the hottest hours",
    "q_proteger_m": "The maximum temperature is {signo}{dif:.1f} °C above normal ({valor:.1f} °C).",
    "q_sembrar": "Plant {rotacion}: it is the rotation with the best score ({p}/100)",
    "q_sembrar_m": "No indicator is at high level and {mes} is a planting month for {cultivo}.",
    "q_esperar_mes": "Wait until {mes} to plant {rotacion}",
    "q_esperar_mes_m": "{mes_hoy} is not a recommended planting month for {cultivo}; no indicator is at high level.",
    "q_plan": "Continue the normal {etapa} management",
    "q_plan_m": "No indicator is at high level.",
    "p_motivo": "{etapa} in {mes}: {razon}",
    "v_evento_2017": "Coastal El Niño 2017",
    "v_accion_mur": "Watch the sea: prepare drainage and don't plant in flood-prone areas",
    "v_accion_drenaje": "Prepare drainage and don't plant in low, flood-prone areas",
    "v_motivo_mur": "The sea in Niño 1+2 reached {signo}{anom:.2f} °C above normal (week of {semana}).",
    "v_accion_lluvia": "Prepare drainage: rainfall is already far above normal",
    "v_motivo_lluvia": "Rainfall in {mes} was {veces:.1f} times normal.",
    "v_nota_lluvia": "Alert computed with rainfall only; with MUR SST it would come earlier",
    "v_resumen": "In {mes} it rained {veces:.1f} times the normal amount ({fuente}). AgroShift would have warned on "
                 "{fecha}, {semanas} weeks earlier.",
    "v_resumen_sin_alerta": "Peak rainfall in {mes} ({veces:.1f} times normal, {fuente}). With the current rules no "
                            "alert would have fired between December and April.",
    "v_sin_alerta": "No alert: follow your usual planting calendar",
    "v_realidad_2017": "Between January and April 2017, coastal El Niño rains caused floods and mudslides along "
                       "Peru's northern coast. In Piura, the Piura River overflowed on March 27, flooding the city "
                       "and Bajo Piura.",
})


def nombre_mes(lang: str, mes: int) -> str:
    return MESES.get(lang, MESES["es"])[mes - 1]
