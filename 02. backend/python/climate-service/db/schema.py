"""Esquema único (SQLAlchemy Core). Nombres en snake_case; el contrato del backend usa camelCase en el JSON,
no en las tablas. La tabla `datosNasa` del contrato se ofrece como la vista `v_datos_nasa`.

Modelo en estrella: dimensiones (region, zona, fuente_dato, variable, cultivo) y hechos
(observacion, indice_climatico, ndvi...). Cada dato guarda su FUENTE y su VERSIÓN: la app puede decir
"humedad del suelo 40 % por debajo de lo normal (SMAP v006)" con respaldo verificable.
"""

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

JSON_T = JSON().with_variant(JSONB(), "postgresql")
metadata = MetaData()

# ------------------------------------------------------------------ dimensiones
region = Table(
    "region", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("codigo", String(30), nullable=False, unique=True),
    Column("nombre", String(80), nullable=False),
)  # fmt: skip

zona = Table(
    "zona", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("nombre", String(120), nullable=False, unique=True),
    Column("region_id", Integer, ForeignKey("region.id"), nullable=False),
    Column("tipo", String(10), nullable=False, server_default="agricola"),
    Column("lat", Float, nullable=False),
    Column("lon", Float, nullable=False),
    Column("aproximada", Boolean, nullable=False, server_default="1"),  # coordenadas por validar (Alejandro)
    Column("elevacion_m", Float),  # SRTM 30 m
    Column("pendiente_pct", Float),  # SRTM 30 m, media en ~150 m
    Column("suelo_ph", Float),  # ISRIC SoilGrids 0-30 cm
    Column("suelo_carbono_g_kg", Float),
    Column("suelo_arcilla_pct", Float),
    Column("suelo_arena_pct", Float),
    CheckConstraint("tipo IN ('agricola','mar')", name="ck_zona_tipo"),
    CheckConstraint("lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180", name="ck_zona_coord"),
)  # fmt: skip

fuente_dato = Table(
    "fuente_dato", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("codigo", String(40), nullable=False, unique=True),
    Column("nombre", String(120), nullable=False),
    Column("institucion", String(80), nullable=False),
    Column("producto", String(60)),
    Column("version", String(20)),
    Column("doi", String(120)),
    Column("resolucion", String(60)),
    Column("cobertura", String(60)),
    Column("url", String(300)),
    Column("acceso", String(80)),
    Column("estado", String(20), nullable=False),  # en_uso | probado | bloqueado | planeado
    Column("nota", Text),
    CheckConstraint("estado IN ('en_uso','probado','bloqueado','planeado')", name="ck_fuente_estado"),
)  # fmt: skip

variable = Table(
    "variable", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("codigo", String(40), nullable=False, unique=True),
    Column("nombre", String(120), nullable=False),
    Column("unidad", String(30), nullable=False),
    Column("fuente_id", Integer, ForeignKey("fuente_dato.id"), nullable=False),
    Column("descripcion", Text),
)  # fmt: skip

cultivo = Table(
    "cultivo", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("nombre", String(80), nullable=False, unique=True),
    Column("tipo", String(12), nullable=False, server_default="anual"),
    Column("temp_min_c", Float, nullable=False),
    Column("temp_max_c", Float, nullable=False),
    Column("agua_necesaria", String(6), nullable=False),
    Column("meses_siembra", JSON_T, nullable=False),
    Column("meses_cosecha", JSON_T, nullable=False),
    Column("acciones_por_etapa", JSON_T),
    Column("es_prueba", Boolean, nullable=False, server_default="1"),  # 1 = dato de prueba, no validado
    Column("fuente", Text),
    CheckConstraint("agua_necesaria IN ('baja','media','alta')", name="ck_cultivo_agua"),
    CheckConstraint("tipo IN ('anual','permanente')", name="ck_cultivo_tipo"),
    CheckConstraint("temp_min_c < temp_max_c", name="ck_cultivo_temp"),
)  # fmt: skip

rotacion = Table(
    "rotacion", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("nombre", String(120), nullable=False),
    Column("cultivo1_id", Integer, ForeignKey("cultivo.id"), nullable=False),
    Column("cultivo2_id", Integer, ForeignKey("cultivo.id"), nullable=False),
    UniqueConstraint("cultivo1_id", "cultivo2_id", name="uq_rotacion_par"),
)  # fmt: skip

# ------------------------------------------------------------------ hechos
observacion = Table(
    "observacion", metadata,
    Column("id", BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True),
    Column("zona_id", Integer, ForeignKey("zona.id"), nullable=False),
    Column("fecha", Date, nullable=False),  # mensual: primer día del mes · compuesta16d: inicio de la compuesta
    Column("escala", String(14), nullable=False),
    Column("variable_id", Integer, ForeignKey("variable.id"), nullable=False),
    Column("valor", Float, nullable=False),
    Column("calidad", String(30)),
    UniqueConstraint("zona_id", "fecha", "escala", "variable_id", name="uq_observacion"),
    CheckConstraint("escala IN ('diaria','mensual','compuesta16d')", name="ck_obs_escala"),
    Index("ix_obs_zona_var_fecha", "zona_id", "variable_id", "fecha"),
)  # fmt: skip

normal_mensual = Table(
    "normal_mensual", metadata,
    Column("zona_id", Integer, ForeignKey("zona.id"), nullable=False),
    Column("variable_id", Integer, ForeignKey("variable.id"), nullable=False),
    Column("mes", Integer, nullable=False),
    Column("media", Float, nullable=False),
    Column("desviacion", Float),
    Column("n_anios", Integer, nullable=False),
    Column("anio_ini", Integer, nullable=False),
    Column("anio_fin", Integer, nullable=False),
    PrimaryKeyConstraint("zona_id", "variable_id", "mes", name="pk_normal_mensual"),
    CheckConstraint("mes BETWEEN 1 AND 12", name="ck_normal_mes"),
)  # fmt: skip

indice_climatico = Table(
    "indice_climatico", metadata,
    Column("codigo", String(20), nullable=False),  # ONI, NINO12, NINO12_ANOM, NINO3_ANOM, NINO34, NINO34_ANOM...
    Column("fecha", Date, nullable=False),
    Column("valor", Float, nullable=False),
    Column("fuente_id", Integer, ForeignKey("fuente_dato.id"), nullable=False),
    PrimaryKeyConstraint("codigo", "fecha", name="pk_indice_climatico"),
)  # fmt: skip

episodio_calido = Table(
    "episodio_calido", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("indice", String(20), nullable=False),
    Column("inicio", Date, nullable=False),
    Column("fin", Date, nullable=False),
    Column("meses", Integer, nullable=False),
    Column("pico_anomalia_c", Float, nullable=False),
    Column("pico_fecha", Date, nullable=False),
    Column("media_anomalia_c", Float, nullable=False),
)  # fmt: skip

sst_clima = Table(
    "sst_clima", metadata,
    Column("zona_id", Integer, ForeignKey("zona.id"), nullable=False),
    Column("doy", Integer, nullable=False),
    Column("media_c", Float, nullable=False),
    Column("n", Integer, nullable=False),
    PrimaryKeyConstraint("zona_id", "doy", name="pk_sst_clima"),
)  # fmt: skip

tendencia = Table(
    "tendencia", metadata,
    Column("zona_id", Integer, ForeignKey("zona.id"), nullable=False),
    Column("variable_id", Integer, ForeignKey("variable.id"), nullable=False),
    Column("anio_ini", Integer, nullable=False),
    Column("anio_fin", Integer, nullable=False),
    Column("metodo", String(40), nullable=False),
    Column("tau", Float),
    Column("p_valor", Float),
    Column("pendiente_sen_por_decada", Float),
    Column("sentido", String(20), nullable=False),
    PrimaryKeyConstraint("zona_id", "variable_id", "metodo", name="pk_tendencia"),
)  # fmt: skip

composite_nino = Table(
    "composite_nino", metadata,
    Column("zona_id", Integer, ForeignKey("zona.id"), nullable=False),
    Column("variable_id", Integer, ForeignKey("variable.id"), nullable=False),
    Column("mes", Integer, nullable=False),
    Column("media_nino", Float, nullable=False),
    Column("media_normal", Float, nullable=False),
    Column("razon", Float),  # media_nino / media_normal
    Column("n_nino", Integer, nullable=False),
    Column("n_normal", Integer, nullable=False),
    PrimaryKeyConstraint("zona_id", "variable_id", "mes", name="pk_composite_nino"),
)  # fmt: skip

validacion_quincena = Table(
    "validacion_quincena", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("zona_id", Integer, ForeignKey("zona.id"), nullable=False),
    Column("evento", String(40), nullable=False),  # p. ej. nino_costero_2017
    Column("desde", Date, nullable=False),
    Column("hasta", Date, nullable=False),
    Column("entrada", JSON_T, nullable=False),  # cuerpo de POST /indicadores
    Column("indicadores", JSON_T, nullable=False),
    Column("rotaciones", JSON_T),
    Column("que_hacer", JSON_T),
    Column("nivel_maximo", String(5), nullable=False),
    Column("advertencias", JSON_T),
    UniqueConstraint("zona_id", "evento", "hasta", name="uq_validacion"),
    CheckConstraint("nivel_maximo IN ('bajo','medio','alto')", name="ck_validacion_nivel"),
)  # fmt: skip

recomendacion_cache = Table(
    "recomendacion_cache", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("zona_id", Integer, ForeignKey("zona.id"), nullable=False),
    Column("fecha", Date, nullable=False),
    Column("payload", JSON_T, nullable=False),  # respuesta completa de /recomendacion (Plan B de la demo)
    Column("creado", DateTime, nullable=False),
    UniqueConstraint("zona_id", "fecha", name="uq_reco_cache"),
)  # fmt: skip

consulta = Table(
    "consulta", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("lat", Float, nullable=False),
    Column("lon", Float, nullable=False),
    Column("fecha", Date, nullable=False),
    Column("rotacion_recomendada_id", Integer, ForeignKey("rotacion.id")),
)  # fmt: skip

# ------------------------------------------------------------------ vistas (SQL estándar: SQLite y PostgreSQL)
VISTAS: dict[str, str] = {
    # La tabla `datosNasa` del contrato (id, lat, lon, fecha, fuente, variable, valor)
    "v_datos_nasa": """
        SELECT o.id, z.lat, z.lon, o.fecha, f.nombre AS fuente, v.codigo AS variable, o.valor
        FROM observacion o
        JOIN zona z ON z.id = o.zona_id
        JOIN variable v ON v.id = o.variable_id
        JOIN fuente_dato f ON f.id = v.fuente_id
    """,
    # Cada observación mensual frente a su normal: anomalía y puntaje z
    "v_anomalia_mensual": """
        SELECT o.zona_id, o.variable_id, o.fecha, o.valor, n.media AS normal, n.desviacion,
               o.valor - n.media AS anomalia,
               (o.valor - n.media) / NULLIF(n.desviacion, 0) AS z
        FROM observacion o
        JOIN normal_mensual n ON n.zona_id = o.zona_id AND n.variable_id = o.variable_id
             AND n.mes = CAST(SUBSTR(CAST(o.fecha AS VARCHAR(10)), 6, 2) AS INTEGER)
        WHERE o.escala = 'mensual'
    """,
    # Último dato de cada zona y variable
    "v_ultimo_dato": """
        SELECT zona_id, variable_id, fecha, valor, escala
        FROM (
            SELECT o.zona_id, o.variable_id, o.fecha, o.valor, o.escala,
                   ROW_NUMBER() OVER (PARTITION BY o.zona_id, o.variable_id ORDER BY o.fecha DESC) AS rn
            FROM observacion o
        ) t
        WHERE rn = 1
    """,
    # Resumen de la validación: nivel más alto por zona y quincena
    "v_validacion_resumen": """
        SELECT z.nombre AS zona, v.evento, v.desde, v.hasta, v.nivel_maximo
        FROM validacion_quincena v JOIN zona z ON z.id = v.zona_id
    """,
}

TABLAS_SEMILLA = ("region", "fuente_dato", "variable", "zona", "cultivo", "rotacion", "normal_mensual", "indice_climatico", "episodio_calido", "tendencia", "composite_nino")
