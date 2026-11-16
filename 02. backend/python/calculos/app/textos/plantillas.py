"""Plantillas de texto es/en (sin IA). Cada frase cita el número que la decidió."""
from __future__ import annotations

Lang = str  # "es" | "en"

UNIDADES = {
    "es": {"lluvia": "mm/día", "humedadSuelo": "fracción 0-1", "calor": "°C", "elNino": "°C sobre lo normal"},
    "en": {"lluvia": "mm/day", "humedadSuelo": "fraction 0-1", "calor": "°C", "elNino": "°C above normal"},
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
        "elnino": "El mar frente a Perú y Ecuador está {valor:.1f} °C {dir} de lo normal (semana del {semana}).",
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
        "elnino": "The sea off Peru and Ecuador is {valor:.1f} °C {dir} normal (week of {semana}).",
        "elnino_sin_datos": "No sea surface temperature data (run scripts/descargar_mur_sst.py).",
        "aviso_imerg_viejo": "Satellite rainfall data is behind: the latest is from {fecha}.",
        "aviso_imerg_sin": "No recent satellite rainfall (last GPM IMERG value: {fecha}). Showing NASA POWER, a model that may overstate rain in Piura.",
    },
}


def fecha_larga(lang: Lang, iso: str) -> str:
    """'2026-11-09' → '9 de noviembre' / 'November 9' (el año solo si no es el actual). Lo que un agricultor lee."""
    from datetime import date
    try:
        d = date.fromisoformat(str(iso)[:10])
    except ValueError:
        return str(iso)
    mes = MESES.get(lang, MESES["es"])[d.month - 1]
    anio = "" if d.year == date.today().year else (f" de {d.year}" if lang == "es" else f", {d.year}")
    return f"{d.day} de {mes}{anio}" if lang == "es" else f"{mes} {d.day}{anio}"


def texto(lang: Lang, clave: str, **kw) -> str:
    # Las fechas de las frases se leen en palabras ("9 de noviembre"), nunca 2026-11-09
    for k in ("semana", "fecha"):
        if isinstance(kw.get(k), str) and len(kw[k]) >= 10 and kw[k][4] == "-":
            kw[k] = fecha_larga(lang, kw[k])
    return TEXTOS.get(lang, TEXTOS["es"])[clave].format(**kw)


def dir_mar(lang: Lang, x: float) -> str:
    """'más caliente' / 'más frío' (o en inglés 'warmer than' / 'colder than') según el signo de la anomalía."""
    if lang == "en":
        return "warmer than" if x >= 0 else "colder than"
    return "más caliente" if x >= 0 else "más frío"


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
    "c_helada": "Riesgo de helada en {mes}: la mínima normal es {t:.1f} °C y puede quemar el {cultivo}.",
    "s_desnudo": "El suelo queda desnudo {n} meses al año: se erosiona y pierde materia orgánica. Siembra una leguminosa o un cultivo de cobertura en ese tiempo.",
    "c_exceso": "En {mes} llueven normalmente {mm:.0f} mm: {veces:.1f} veces lo que necesita el {cultivo}.",
    "c_deficit": "En {mes} llueven normalmente {mm:.0f} mm de los ~{nec:.0f} que necesita el {cultivo}: depende del riego.",
    "c_ok": "El clima normal de {mes} está dentro de lo que tolera el {cultivo}.",
    "c_nino": "El Niño (el mar está {anom:.1f} °C más caliente) sube el riesgo de lluvias.",
    "c_exceso_nino": "En {mes} llueven normalmente {mm:.0f} mm, pero con El Niño (el mar está {anom:.1f} °C más "
                     "caliente) pueden venir lluvias fuertes.",
    "c_sin_nino": "Sin señal de El Niño disponible.",
    # Rotaciones
    "r_ok": "Por el clima no pierde puntos: la campaña le favorece.",
    "r_pierde": "Por el clima pierde {p} puntos, sobre todo por {razon}.",
    "r_agua": "su alto uso de agua con {ind} en déficit",
    "r_temp": "{n} mes(es) fuera de su rango de temperatura",
    "r_alto": "{n} mes(es) de la campaña con riesgo alto",
    "r_medio": "{n} mes(es) de la campaña con riesgo medio",
    # Rotación de siempre: una frase con las causas de los tres puntajes
    "t_buena": "Buena opción este año, aunque {razones}.",
    "t_regular": "Regular este año: {razones}.",
    "t_riesgosa": "Muy riesgosa este año: {razones}.",
    "t_nino": "viene El Niño (el mar está {anom:.1f} °C más caliente)",
    "t_agua": "usa mucha agua",
    "t_repetir": "repetir {cultivo} cansa el suelo y deja sus plagas",
    "t_epoca": "no es su época de siembra",
    "v_def_evento": "Evento = lluvia de febrero a abril de {veces:.0f} o más veces la normal (mismo dato satelital).",
    "esc_sin_efecto": "Con este escenario no cambia ningún mes ni ningún puntaje: aquí casi no llueve en esa época "
                      "y el riesgo depende del riego, no de la lluvia.",
    "elnino_hipotetico": "Simulación: el mar {valor:.1f} °C {dir} de lo normal (no es un dato medido).",
    "elnino_contraste_ok": "Otro centro de medición (NOAA, de EE. UU.) ve lo mismo: {valor:.1f} °C.",
    "elnino_contraste_no": "Otro centro de medición (NOAA, de EE. UU.) ve un valor distinto ({valor:.1f} °C): confirma con el ENFEN o tu agencia agraria.",
    "r_siembra": "sembrar {cultivo} fuera de sus meses recomendados",
    "r_nino_extremo": "El Niño: el mar está {anom:.1f} °C más caliente y pueden venir lluvias e inundaciones",
    "r_tradicional": " Es lo que se siembra siempre en tu zona: la mostramos para comparar.",
    # Salud del suelo
    "s_monocultivo": "Repetir {cultivo} agota los mismos nutrientes del suelo y mantiene sus plagas.",
    "s_familia": "{a} y {b} son de la misma familia ({familia}): sacan los mismos nutrientes y comparten plagas.",
    "s_leguminosa": "{cultivo} es leguminosa: fija nitrógeno del aire en el suelo.",
    "s_raices": "Raíces de distinta profundidad ({a}: {pa}; {b}: {pb}) aprovechan capas distintas del suelo.",
    "s_cobertura": "{cultivo} cubre el suelo y lo protege de la erosión y el sol.",
    "s_agua_salino": "{cultivo} usa mucha agua: en tu suelo salino el riego intenso aumenta las sales.",
    "raiz_superficial": "superficial", "raiz_media": "media", "raiz_profunda": "profunda",
    "s_tolerancia_sal": "{cultivo} tolera {tol} la sal: en tu suelo salino rinde menos.",
    "s_agua_seguidos": "{a} y {b} usan mucha agua, uno tras otro: tanto riego cansa el suelo y lo puede salinizar.",
    "tol_baja": "poco", "tol_media": "a medias", "tol_alta": "bien",
    "s_arenoso": "{cultivo} necesita mucha agua y tu suelo arenoso la retiene poco.",
    "p_arriesgar_menos": "Te la recomendamos porque elegiste arriesgar menos: es la que mejor combina el clima esperado ({clima} de 100) con el resto.",
    "p_cuidar_suelo": "Te la recomendamos porque elegiste cuidar el suelo: cuida tu suelo con {suelo} de 100.",
    "p_ahorrar_agua": "Te la recomendamos porque elegiste ahorrar agua: su uso de agua es {agua}.",
    "agua_bajo": "bajo", "agua_medio": "medio", "agua_alto": "alto",
    "ind_lluvia": "la lluvia", "ind_humedadSuelo": "la humedad del suelo",
    # Qué hacer esta quincena
    "q_drenaje": "Prepara los drenajes y no siembres en zonas bajas que se inundan",
    "q_drenaje_m": "El mar frente a Perú y Ecuador está {anom:.1f} °C más caliente de lo normal (semana del {semana}): "
                   "es El Niño y pueden venir lluvias fuertes.",
    "q_esperar_seco": "Espera para sembrar: el suelo está seco",
    "q_regar": "Riega tu {cultivo}: el suelo está seco",
    "q_seco_m": "{ind} está {abs:.0f} % por debajo de lo normal.",
    "q_proteger": "Protege el cultivo del calor: riega temprano y evita trabajar en las horas de más sol",
    "q_proteger_m": "La temperatura máxima está {signo}{dif:.1f} °C sobre lo normal ({valor:.1f} °C).",
    "q_sembrar": "Siembra {rotacion}: es la mejor opción para tu parcela",
    "q_sembrar_m": "Ningún indicador está en nivel alto y {mes} es mes de siembra de {cultivo}.",
    "q_esperar_mes": "Espera a {mes} para sembrar {rotacion}",
    "q_esperar_mes_m": "{mes_hoy} no es mes de siembra recomendado de {cultivo}; ningún indicador está en nivel alto.",
    "q_plan": "Sigue el manejo normal de {etapa}",
    "q_plan_m": "Ningún indicador está en nivel alto.",
    # Permanentes
    "p_motivo": "{etapa} en {mes}: {razon}",
    # Validación
    "v_evento_2017": "El Niño costero 2017",
    "v_accion_mur": "Vigila el mar: el agua se está calentando. Revisa tus drenajes y prepárate por si llega El Niño",
    "v_accion_drenaje": "Prepara los drenajes y no siembres en zonas bajas que se inundan",
    "v_motivo_mur": "El mar frente a la costa llegó a {anom:.1f} °C más caliente de lo normal (semana del {semana}).",
    "v_accion_lluvia": "Prepara drenajes: la lluvia ya está muy por encima de lo normal",
    "v_motivo_lluvia": "La lluvia de {mes} fue {veces:.1f} veces lo normal.",
    "v_nota_lluvia": "Alerta calculada solo con la lluvia; con la temperatura del mar llegaría antes",
    "v_resumen": "En {mes} llovió {veces:.1f} veces lo normal ({fuente}). AllpaShift habría alertado el {fecha}, "
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
    "c_helada": "Frost risk in {mes}: the normal minimum is {t:.1f} °C and can burn {cultivo}.",
    "s_desnudo": "The soil is bare {n} months a year: it erodes and loses organic matter. Plant a legume or a cover crop in that time.",
    "c_exceso": "{mes} normally gets {mm:.0f} mm of rain: {veces:.1f} times what {cultivo} needs.",
    "c_deficit": "{mes} normally gets {mm:.0f} mm of the ~{nec:.0f} mm {cultivo} needs: it depends on irrigation.",
    "c_ok": "The normal climate in {mes} is within what {cultivo} tolerates.",
    "c_nino": "El Niño (the sea is {anom:.1f} °C warmer) raises the rain risk.",
    "c_exceso_nino": "{mes} normally gets {mm:.0f} mm, but with El Niño (the sea is {anom:.1f} °C warmer) heavy rain may come.",
    "c_sin_nino": "No El Niño signal available.",
    "r_ok": "Climate takes no points off: the season suits it.",
    "r_pierde": "Climate takes off {p} points, mainly because of {razon}.",
    "r_agua": "its high water use with {ind} in deficit",
    "r_temp": "{n} month(s) outside its temperature range",
    "r_alto": "{n} month(s) of the season at high risk",
    "r_medio": "{n} month(s) of the season at medium risk",
    "t_buena": "A good option this year, although {razones}.",
    "t_regular": "Fair this year: {razones}.",
    "t_riesgosa": "Very risky this year: {razones}.",
    "t_nino": "El Niño is coming (the sea is {anom:.1f} °C warmer)",
    "t_agua": "it uses a lot of water",
    "t_repetir": "repeating {cultivo} tires the soil and keeps its pests",
    "t_epoca": "it is not its planting season",
    "v_def_evento": "Event = February–April rainfall of {veces:.0f} or more times normal (same satellite data).",
    "esc_sin_efecto": "This scenario changes no month and no score: it barely rains here at that time of year, "
                      "so the risk depends on irrigation, not rainfall.",
    "elnino_hipotetico": "Simulation: the sea {valor:.1f} °C {dir} normal (not measured data).",
    "elnino_contraste_ok": "Another measuring center (NOAA, USA) sees the same: {valor:.1f} °C.",
    "elnino_contraste_no": "Another measuring center (NOAA, USA) sees a different value ({valor:.1f} °C): check with ENFEN or your farm agency.",
    "r_siembra": "planting {cultivo} outside its recommended months",
    "r_nino_extremo": "El Niño: the sea is {anom:.1f} °C warmer and rain and floods may come",
    "r_tradicional": " It is what is always planted in your area: shown for comparison.",
    # Soil health
    "s_monocultivo": "Repeating {cultivo} drains the same soil nutrients and keeps its pests.",
    "s_familia": "{a} and {b} are from the same family ({familia}): they take the same nutrients and share pests.",
    "s_leguminosa": "{cultivo} is a legume: it fixes nitrogen from the air into the soil.",
    "s_raices": "Roots at different depths ({a}: {pa}; {b}: {pb}) use different soil layers.",
    "s_cobertura": "{cultivo} covers the soil and protects it from erosion and sun.",
    "s_agua_salino": "{cultivo} uses a lot of water: in your saline soil heavy irrigation raises the salts.",
    "raiz_superficial": "shallow", "raiz_media": "medium", "raiz_profunda": "deep",
    "s_tolerancia_sal": "{cultivo} tolerates salt {tol}: in your saline soil it yields less.",
    "s_agua_seguidos": "{a} and {b} both need a lot of water, one after the other: so much irrigation wears out the soil and can make it salty.",
    "tol_baja": "poorly", "tol_media": "moderately", "tol_alta": "well",
    "s_arenoso": "{cultivo} needs a lot of water and your sandy soil holds little of it.",
    "p_arriesgar_menos": "Recommended because you chose to take less risk: it best combines the expected climate ({clima} out of 100) with the rest.",
    "p_cuidar_suelo": "Recommended because you chose to care for the soil: it scores {suelo} out of 100 for your soil.",
    "p_ahorrar_agua": "Recommended because you chose to save water: its water use is {agua}.",
    "agua_bajo": "low", "agua_medio": "medium", "agua_alto": "high",
    "ind_lluvia": "rainfall", "ind_humedadSuelo": "soil moisture",
    "q_drenaje": "Prepare drainage and don't plant in low, flood-prone areas",
    "q_drenaje_m": "The sea off Peru and Ecuador is {anom:.1f} °C warmer than normal (week of {semana}): it is El Niño and heavy rain may come.",
    "q_esperar_seco": "Wait to plant: the soil is dry",
    "q_regar": "Irrigate your {cultivo}: the soil is dry",
    "q_seco_m": "{ind} is {abs:.0f}% below normal.",
    "q_proteger": "Protect the crop from heat: irrigate early and avoid working in the hottest hours",
    "q_proteger_m": "The maximum temperature is {signo}{dif:.1f} °C above normal ({valor:.1f} °C).",
    "q_sembrar": "Plant {rotacion}: it is the best option for your plot",
    "q_sembrar_m": "No indicator is at high level and {mes} is a planting month for {cultivo}.",
    "q_esperar_mes": "Wait until {mes} to plant {rotacion}",
    "q_esperar_mes_m": "{mes_hoy} is not a recommended planting month for {cultivo}; no indicator is at high level.",
    "q_plan": "Continue the normal {etapa} management",
    "q_plan_m": "No indicator is at high level.",
    "p_motivo": "{etapa} in {mes}: {razon}",
    "v_evento_2017": "Coastal El Niño 2017",
    "v_accion_mur": "Watch the sea: the water is warming. Check your drains and get ready in case El Niño comes",
    "v_accion_drenaje": "Prepare drainage and don't plant in low, flood-prone areas",
    "v_motivo_mur": "The sea off the coast reached {anom:.1f} °C warmer than normal (week of {semana}).",
    "v_accion_lluvia": "Prepare drainage: rainfall is already far above normal",
    "v_motivo_lluvia": "Rainfall in {mes} was {veces:.1f} times normal.",
    "v_nota_lluvia": "Alert computed with rainfall only; with sea temperature it would come earlier",
    "v_resumen": "In {mes} it rained {veces:.1f} times the normal amount ({fuente}). AllpaShift would have warned on "
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
