"""Umbrales y pesos del modelo de riesgo de AgroShift.

TODO el modelo vive aquí, como números simples, para que cualquiera del equipo (y el jurado)
pueda leerlos y verificarlos. No hay "caja negra": nivel = función de la anomalía, y
puntaje = 100 menos puntos de descuento por cada choque entre clima y cultivo.

Los valores son un PUNTO DE PARTIDA razonable. Se afinan con Alejandro (catálogo y calendarios)
y con la validación de El Niño costero 2017 (ver etl/build_backup.py).
"""

NIVELES = ("bajo", "medio", "alto")

# ---------------------------------------------------------------- anomalías -> nivel
# Cada par es (desde_medio, desde_alto): la anomalía debe ser >= al valor para subir de nivel.

# Lluvia: |valor - normal| / max(normal, piso). Cuenta tanto el déficit como el exceso.
# El piso evita que la anomalía explote donde casi nunca llueve (costa de Piura: normal ~0,1-1,5 mm/día).
# Con piso 3 mm/día, en zonas áridas el nivel medio empieza en +0,75 mm/día y el alto en +1,5 mm/día
# sobre lo normal (≈ 10 y 21 mm extra en 14 días); un déficit de 0,5 mm/día ya no dispara alertas.
LLUVIA_NORMAL_MIN_MM = 3.0
LLUVIA_REL = (0.25, 0.50)

# Humedad del suelo: déficit relativo (normal - valor) / normal. Solo el déficit sube el nivel.
HUMEDAD_DEFICIT_REL = (0.15, 0.30)

# Calor: tempMaxC actual menos tempMaxC normal, en °C. Solo el exceso de calor sube el nivel.
CALOR_ANOMALIA_C = (1.5, 4.0)

# El Niño: anomalía de la temperatura del mar (MUR SST), en °C. Solo el calentamiento sube el nivel.
EL_NINO_SST_C = (0.5, 1.5)

# ---------------------------------------------------------------- fuentes y unidades por defecto
FUENTES = {
    "lluvia": "GPM IMERG",
    "humedadSuelo": "SMAP",
    "calor": "NASA POWER",
    "elNino": "MUR SST",
}
UNIDADES = {
    "lluvia": "mm/día",
    "humedadSuelo": "m3/m3",
    "calor": "°C",
    "elNino": "°C anomalía",
}

# ---------------------------------------------------------------- puntaje de rotación (0-100)
# Se parte de 100 y se descuentan puntos. Cada tabla se lee: PUNTOS[necesidad de agua][nivel].
SEQUIA_PTS = {
    "alta": {"bajo": 0, "medio": 25, "alto": 55},
    "media": {"bajo": 0, "medio": 12, "alto": 28},
    "baja": {"bajo": 0, "medio": 4, "alto": 10},
}
# Si falta lluvia (pero el suelo no lo dice), cuenta como esta fracción de la tabla de sequía.
LLUVIA_DEFICIT_FACTOR = 0.3

# Exceso de lluvia. SUPUESTO: los cultivos de poca agua sufren más con el encharcamiento y el
# arroz lo tolera. Se reemplaza por un campo del catálogo (toleraInundacion) si Alejandro lo agrega.
EXCESO_PTS = {"bajo": 0, "medio": 10, "alto": 25}
EXCESO_FACTOR = {"baja": 1.0, "media": 0.75, "alta": 0.25}
# Exceso EXTREMO (anomalía relativa >= +200 %): inundación y desborde de ríos, como el Niño costero de
# marzo 2017 (+800 % en Bajo Piura). Daña a TODOS los cultivos, también al arroz: se ignora el factor.
LLUVIA_EXCESO_EXTREMO_REL = 2.0
EXCESO_EXTREMO_PTS = 60

# Calor: puntos por nivel + puntos por cada °C que la temperatura actual pasa del tempMaxC del cultivo.
CALOR_NIVEL_PTS = {"bajo": 0, "medio": 8, "alto": 18}
CALOR_PTS_POR_C_SOBRE_LIMITE = 4
CALOR_MARGEN_SEGURO_C = 2  # si el cultivo tiene más de 2 °C de margen, el calor casi no le afecta
CALOR_FACTOR_CON_MARGEN = 0.25
CALOR_MAX_PTS = 35

# Señal de El Niño: anticipa exceso de lluvia en los próximos meses (mismo factor que el exceso).
EL_NINO_PTS = {"bajo": 0, "medio": 4, "alto": 10}
# Señal EXTRAORDINARIA (>= +3 °C en el mar): en el registro NOAA 1982-2026 solo la superan 1982-83, 1997-98 y 2023-26, años de
# lluvias e inundaciones catastróficas en el norte. Afecta a TODOS los cultivos (también al arroz): se ignora el factor.
# SUPUESTO por validar con ENFEN / la mentoría agro-clima.
EL_NINO_EXTREMO_C = 3.0
EL_NINO_EXTREMO_PTS = 35

# Sembrar fuera de la ventana de siembra del catálogo (solo cuenta para el primer cultivo).
FUERA_DE_TEMPORADA_PTS = 15

# El primer cultivo es la decisión de ahora; el segundo viene después y depende menos del clima de hoy.
PESO_CULTIVO1 = 0.65
PESO_CULTIVO2 = 0.35

# Repetir el mismo cultivo (monocultivo) no corta el ciclo de plagas ni mejora el suelo: el reto
# pide justamente rotar. Descuento fijo y pequeño; también sirve de desempate cuando el clima es normal.
MONOCULTIVO_PTS = 5

# Un descuento menor a esto no se menciona en la explicación.
DESCUENTO_MINIMO_EXPLICADO = 3.0

# ---------------------------------------------------------------- incertidumbre (opcional: "incertidumbre": true)
# Error típico de cada dato satelital (1 σ). El puntaje se recalcula con todos los indicadores empujados K·σ hacia el
# lado malo (puntajeMin) y hacia el lado bueno (puntajeMax). Referencias: SMAP exige ubRMSE <= 0,04 m3/m3.
INCERTIDUMBRE_K = 1.0
INCERTIDUMBRE = {
    "lluvia": ("rel", 0.25),  # 25 % del valor (error típico de la lluvia de satélite frente a pluviómetros)
    "humedadSuelo": ("abs", 0.04),  # m3/m3
    "calor": ("abs", 1.5),  # °C (temperatura en rejilla frente a estación)
    "elNino": ("abs", 0.3),  # °C
}
CONFIANZA_ALTA_HASTA = 10  # ancho del rango (puntajeMax - puntajeMin) hasta el cual la confianza es alta
CONFIANZA_MEDIA_HASTA = 25

# Riesgo de la rotación según su puntaje
RIESGO_BAJO_DESDE = 70
RIESGO_MEDIO_DESDE = 45
