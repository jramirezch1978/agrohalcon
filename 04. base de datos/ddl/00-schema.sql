-- ============================================================================
-- AllpaShift - Modelo relacional PostgreSQL 17 (v2, 2026-11-14)
-- Respeta las 5 tablas del "Contrato del backend": cultivos, rotaciones, zonas,
-- datos_nasa y consultas (nombres en snake_case para Spring/JPA).
--
-- Esquemas:
--   agro : territorio (regiones, zonas/valles), cultivos, calendario, acciones,
--          rotaciones, parcelas, consultas y riesgo mensual de campana
--   nasa : datasets NASA, datos por punto/fecha, normales, eventos El Nino, cache
--   ref  : referencias cientificas (papers MDPI, datasets) para "References"
-- Documentacion: 01. documentacion/26_modelo_base_de_datos.md
-- ============================================================================
SET client_min_messages = warning;

CREATE SCHEMA IF NOT EXISTS agro;
CREATE SCHEMA IF NOT EXISTS nasa;
CREATE SCHEMA IF NOT EXISTS ref;

-- ---------------------------------------------------------------------------
-- 1. Territorio
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agro.regiones (
    id          SMALLSERIAL PRIMARY KEY,
    codigo      VARCHAR(20)  NOT NULL UNIQUE,          -- 'piura', 'la_libertad' (igual que zonas.region del contrato)
    nombre      VARCHAR(60)  NOT NULL UNIQUE,
    lat         NUMERIC(8,5),
    lon         NUMERIC(8,5)
);

-- Contrato: zonas (id, nombre, lat, lon, region). Una zona es un valle o zona agricola.
CREATE TABLE IF NOT EXISTS agro.zonas (
    id                 SERIAL PRIMARY KEY,
    nombre             VARCHAR(80)  NOT NULL UNIQUE,
    lat                NUMERIC(8,5) NOT NULL,
    lon                NUMERIC(8,5) NOT NULL,
    region             VARCHAR(20)  NOT NULL REFERENCES agro.regiones(codigo) ON UPDATE CASCADE,
    piso               VARCHAR(10)  NOT NULL DEFAULT 'costa' CHECK (piso IN ('costa', 'sierra', 'selva')),
    altitud_m          INTEGER,
    cuenca             VARCHAR(80),                     -- Piura, Chira, Chancay-Lambayeque...
    geojson            JSONB,                           -- poligono (GeoMIDAGRI) opcional; PostGIS no es obligatorio
    coordenadas_validadas BOOLEAN NOT NULL DEFAULT FALSE,
    fuente             VARCHAR(200)
);

-- ---------------------------------------------------------------------------
-- 2. Cultivos
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agro.grupos_cultivo (
    id      SMALLSERIAL PRIMARY KEY,
    codigo  VARCHAR(20) NOT NULL UNIQUE,                -- cereal, menestra, frutal, hortaliza, tuberculo, industrial
    nombre  VARCHAR(40) NOT NULL
);

-- Contrato: cultivos (id, nombre, tempMinC, tempMaxC, aguaNecesaria, mesesSiembra, mesesCosecha, accionesPorEtapa).
-- mesesSiembra / mesesCosecha / accionesPorEtapa se derivan del calendario y las acciones (vista agro.v_cultivos_contrato).
CREATE TABLE IF NOT EXISTS agro.cultivos (
    id                 SERIAL PRIMARY KEY,
    nombre             VARCHAR(80)  NOT NULL UNIQUE,
    nombre_cientifico  VARCHAR(120),
    grupo_id           SMALLINT     NOT NULL REFERENCES agro.grupos_cultivo(id),
    tipo               VARCHAR(15)  NOT NULL CHECK (tipo IN ('anual', 'semipermanente', 'permanente')),
    temp_min_c         NUMERIC(4,1),
    temp_max_c         NUMERIC(4,1),
    agua_necesaria     VARCHAR(5)   NOT NULL CHECK (agua_necesaria IN ('baja', 'media', 'alta')),
    agua_mm_min        INTEGER,
    agua_mm_max        INTEGER,
    ciclo_dias         INTEGER,                         -- anual: siembra->cosecha; permanente: NULL
    kc_inicial         NUMERIC(3,2),
    kc_medio           NUMERIC(3,2),
    kc_final           NUMERIC(3,2),
    fija_nitrogeno     BOOLEAN NOT NULL DEFAULT FALSE,
    cultivo_cobertura  BOOLEAN NOT NULL DEFAULT FALSE,
    raiz_profunda      BOOLEAN NOT NULL DEFAULT FALSE,
    tolera_sequia      BOOLEAN NOT NULL DEFAULT FALSE,
    tolera_inundacion  BOOLEAN NOT NULL DEFAULT FALSE,
    rota               BOOLEAN GENERATED ALWAYS AS (tipo = 'anual') STORED,  -- permanentes reciben acciones, no rotaciones
    fuente             VARCHAR(250),
    validado           BOOLEAN NOT NULL DEFAULT FALSE   -- TRUE cuando Alejandro lo valida con MIDAGRI / FAO
);

-- Salud del suelo (rotaciones): columnas opcionales; NULL = sin dato. Valores en seed/03-salud-suelo.sql.
ALTER TABLE agro.cultivos ADD COLUMN IF NOT EXISTS familia VARCHAR(40);                 -- familia botánica (Poaceae, Fabaceae...)
ALTER TABLE agro.cultivos ADD COLUMN IF NOT EXISTS profundidad_raiz VARCHAR(12)
    CHECK (profundidad_raiz IN ('superficial', 'media', 'profunda'));
ALTER TABLE agro.cultivos ADD COLUMN IF NOT EXISTS tolerancia_salinidad VARCHAR(5)
    CHECK (tolerancia_salinidad IN ('baja', 'media', 'alta'));
ALTER TABLE agro.cultivos ADD COLUMN IF NOT EXISTS es_leguminosa BOOLEAN
    GENERATED ALWAYS AS (familia = 'Fabaceae') STORED;

-- En que zonas se siembra cada cultivo y con que superficie (DRAP / MIDAGRI SIEA)
CREATE TABLE IF NOT EXISTS agro.cultivos_zona (
    cultivo_id     INTEGER  NOT NULL REFERENCES agro.cultivos(id) ON DELETE CASCADE,
    zona_id        INTEGER  NOT NULL REFERENCES agro.zonas(id)    ON DELETE CASCADE,
    campania       VARCHAR(9) NOT NULL DEFAULT '2025-2026',
    superficie_ha  NUMERIC(10,1),
    principal      BOOLEAN NOT NULL DEFAULT FALSE,
    fuente         VARCHAR(200),
    PRIMARY KEY (cultivo_id, zona_id, campania)
);

-- Superficie a nivel de region cuando no hay desglose por valle
CREATE TABLE IF NOT EXISTS agro.superficie_region (
    cultivo_id     INTEGER  NOT NULL REFERENCES agro.cultivos(id) ON DELETE CASCADE,
    region         VARCHAR(20) NOT NULL REFERENCES agro.regiones(codigo),
    campania       VARCHAR(9) NOT NULL,
    superficie_ha  NUMERIC(10,1) NOT NULL,
    fuente         VARCHAR(200),
    PRIMARY KEY (cultivo_id, region, campania)
);

-- ---------------------------------------------------------------------------
-- 3. Calendario y acciones ("Que hago esta quincena?")
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agro.fases (
    codigo  CHAR(1)     PRIMARY KEY,                    -- S C F K D
    nombre  VARCHAR(20) NOT NULL
);

-- Fase por mes. zona_id NULL = calendario general del piso (costa/sierra/selva)
CREATE TABLE IF NOT EXISTS agro.calendario (
    id          SERIAL PRIMARY KEY,
    cultivo_id  INTEGER  NOT NULL REFERENCES agro.cultivos(id) ON DELETE CASCADE,
    piso        VARCHAR(10) NOT NULL CHECK (piso IN ('costa', 'sierra', 'selva')),
    zona_id     INTEGER  REFERENCES agro.zonas(id) ON DELETE CASCADE,
    mes         SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    fase        CHAR(1)  NOT NULL REFERENCES agro.fases(codigo),
    UNIQUE NULLS NOT DISTINCT (cultivo_id, piso, zona_id, mes)
);

CREATE TABLE IF NOT EXISTS agro.acciones_etapa (
    id           SERIAL PRIMARY KEY,
    cultivo_id   INTEGER REFERENCES agro.cultivos(id) ON DELETE CASCADE,  -- NULL = aplica a todos
    fase         CHAR(1) NOT NULL REFERENCES agro.fases(codigo),
    quincena     SMALLINT CHECK (quincena IN (1, 2)),                     -- NULL = todo el mes
    descripcion  VARCHAR(300) NOT NULL,
    alerta_nasa  VARCHAR(200),
    indicador    VARCHAR(40),                                             -- lluvia, humedad_suelo, calor, ndvi, sst
    UNIQUE NULLS NOT DISTINCT (cultivo_id, fase, descripcion)
);

-- ---------------------------------------------------------------------------
-- 4. Rotaciones (contrato: id, nombre, cultivo1Id, cultivo2Id)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agro.rotaciones (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(120) NOT NULL UNIQUE,
    cultivo1_id  INTEGER NOT NULL REFERENCES agro.cultivos(id),
    cultivo2_id  INTEGER NOT NULL REFERENCES agro.cultivos(id),
    cultivo3_id  INTEGER REFERENCES agro.cultivos(id),                    -- opcional (rotacion de 3)
    piso         VARCHAR(10) CHECK (piso IN ('costa', 'sierra', 'selva')),
    beneficios   VARCHAR(300),
    sacrificios  VARCHAR(300),
    es_monocultivo BOOLEAN GENERATED ALWAYS AS (cultivo1_id = cultivo2_id) STORED  -- p. ej. Arroz -> Arroz (rotacion actual a comparar)
);

-- ---------------------------------------------------------------------------
-- 5. Parcelas, consultas y riesgo de campana
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agro.parcelas (
    id                  BIGSERIAL PRIMARY KEY,
    nombre              VARCHAR(100),
    lat                 NUMERIC(8,5) NOT NULL,
    lon                 NUMERIC(8,5) NOT NULL,
    zona_id             INTEGER REFERENCES agro.zonas(id),
    area_ha             NUMERIC(8,2),
    cultivo_actual_id   INTEGER REFERENCES agro.cultivos(id),
    rotacion_actual_id  INTEGER REFERENCES agro.rotaciones(id),
    fecha_siembra       DATE,
    creado_en           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Contrato: consultas (id, lat, lon, fecha, rotacionRecomendadaId) + historial completo
CREATE TABLE IF NOT EXISTS agro.consultas (
    id                         BIGSERIAL PRIMARY KEY,
    lat                        NUMERIC(8,5) NOT NULL,
    lon                        NUMERIC(8,5) NOT NULL,
    fecha                      DATE NOT NULL DEFAULT current_date,
    rotacion_recomendada_id    INTEGER REFERENCES agro.rotaciones(id),
    zona_id                    INTEGER REFERENCES agro.zonas(id),
    parcela_id                 BIGINT  REFERENCES agro.parcelas(id) ON DELETE SET NULL,
    indicadores                JSONB,                 -- lo que devolvio climate-service
    resultado                  JSONB,                 -- recomendacion completa mostrada al usuario
    tipo                       VARCHAR(20),           -- recomendacion | mapa | validacion
    clave                      VARCHAR(160),          -- punto + parametros: Java busca aqui antes de pedir a Python (doc 29)
    contrato                   JSONB,                 -- respuesta en forma del contrato (la usa el asistente)
    creado_en                  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_consultas_fecha ON agro.consultas (fecha);
ALTER TABLE agro.consultas ADD COLUMN IF NOT EXISTS tipo VARCHAR(20);
ALTER TABLE agro.consultas ADD COLUMN IF NOT EXISTS clave VARCHAR(160);
ALTER TABLE agro.consultas ADD COLUMN IF NOT EXISTS contrato JSONB;
CREATE INDEX IF NOT EXISTS ix_consultas_clave ON agro.consultas (clave, creado_en DESC);

-- "Perspectiva de la campana": riesgo de cada mes del ciclo (verde / ambar / rojo)
CREATE TABLE IF NOT EXISTS agro.riesgo_mensual (
    zona_id      INTEGER  NOT NULL REFERENCES agro.zonas(id) ON DELETE CASCADE,
    cultivo_id   INTEGER  NOT NULL REFERENCES agro.cultivos(id) ON DELETE CASCADE,
    anio         SMALLINT NOT NULL,
    mes          SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    nivel        VARCHAR(5) NOT NULL CHECK (nivel IN ('verde', 'ambar', 'rojo')),
    puntaje      NUMERIC(5,2),
    motivo       VARCHAR(200),
    detalle      JSONB,
    calculado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (zona_id, cultivo_id, anio, mes)
);

-- ---------------------------------------------------------------------------
-- 6. Datos NASA
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nasa.datasets (
    id           SMALLSERIAL PRIMARY KEY,
    codigo       VARCHAR(40)  NOT NULL UNIQUE,         -- short_name de CMR: SPL3SMP_E, GPM_3IMERGM...
    nombre       VARCHAR(120) NOT NULL,
    fuente       VARCHAR(30)  NOT NULL,                -- valor usado en datos_nasa.fuente
    version      VARCHAR(10),
    doi          VARCHAR(80),
    proveedor    VARCHAR(40),                          -- GES DISC, NSIDC, LP DAAC, PO.DAAC, LaRC
    resolucion   VARCHAR(30),
    requiere_login BOOLEAN NOT NULL DEFAULT FALSE,
    uso          VARCHAR(200)
);

-- Contrato: datosNasa (id, lat, lon, fecha, fuente, variable, valor). Formato del CSV de David (\copy directo).
CREATE TABLE IF NOT EXISTS nasa.datos_nasa (
    id          BIGSERIAL PRIMARY KEY,
    lat         DOUBLE PRECISION NOT NULL,
    lon         DOUBLE PRECISION NOT NULL,
    fecha       DATE NOT NULL,                         -- dia, o primer dia del mes para valores mensuales
    fuente      TEXT NOT NULL,                         -- 'NASA POWER', 'GPM IMERG', 'SMAP', 'MODIS NDVI', 'MUR SST'
    variable    TEXT NOT NULL,                         -- 'NOMBRE_NASA:campoContrato', p. ej. 'PRECTOTCORR:lluviaMm'
    valor       DOUBLE PRECISION NOT NULL,
    version     VARCHAR(10),
    zona_id     INTEGER REFERENCES agro.zonas(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_datos_nasa_punto_fecha ON nasa.datos_nasa (lat, lon, fecha);
CREATE INDEX IF NOT EXISTS idx_datos_nasa_zona ON nasa.datos_nasa (zona_id, variable, fecha);

-- Normal climatologico por zona, variable y mes (1991-2020 segun David)
CREATE TABLE IF NOT EXISTS nasa.normales (
    zona_id   INTEGER  NOT NULL REFERENCES agro.zonas(id) ON DELETE CASCADE,
    variable  TEXT     NOT NULL,
    mes       SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    valor     DOUBLE PRECISION NOT NULL,
    periodo   VARCHAR(9) NOT NULL DEFAULT '1991-2020',
    fuente    TEXT NOT NULL DEFAULT 'NASA POWER',
    PRIMARY KEY (zona_id, variable, mes, periodo)
);

-- Eventos El Nino (costero / global) para la "maquina del tiempo"
CREATE TABLE IF NOT EXISTS nasa.eventos_enso (
    id           SMALLSERIAL PRIMARY KEY,
    nombre       VARCHAR(60) NOT NULL UNIQUE,
    tipo         VARCHAR(10) NOT NULL CHECK (tipo IN ('costero', 'global')),
    inicio       DATE NOT NULL,
    fin          DATE,
    intensidad   VARCHAR(15),
    descripcion  VARCHAR(300),
    fuente       VARCHAR(200)
);

-- Cache de respuestas HTTP de las APIs (POWER, CMR, ERDDAP...)
CREATE TABLE IF NOT EXISTS nasa.respuesta_cache (
    id          BIGSERIAL PRIMARY KEY,
    fuente      VARCHAR(30)  NOT NULL,
    clave       VARCHAR(300) NOT NULL,
    respuesta   JSONB        NOT NULL,
    obtenido_en TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (fuente, clave)
);

-- ---------------------------------------------------------------------------
-- 7. Referencias (seccion References de la entrega)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ref.referencias (
    id        SERIAL PRIMARY KEY,
    tipo      VARCHAR(10) NOT NULL CHECK (tipo IN ('paper', 'dataset', 'web', 'oficial')),
    tema      VARCHAR(80),
    cita      TEXT NOT NULL,
    doi       VARCHAR(80) UNIQUE,
    url       TEXT,
    licencia  VARCHAR(20),
    archivo   VARCHAR(200)                             -- ruta del PDF en 01. documentacion/papers
);

-- ---------------------------------------------------------------------------
-- 8. Vistas con la forma exacta del contrato (camelCase en el JSON lo pone Java)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW agro.v_cultivos_contrato AS
SELECT c.id,
       c.nombre,
       c.temp_min_c,
       c.temp_max_c,
       c.agua_necesaria,
       COALESCE((SELECT array_agg(DISTINCT k.mes ORDER BY k.mes) FROM agro.calendario k WHERE k.cultivo_id = c.id AND k.zona_id IS NULL AND k.fase = 'S'), '{}') AS meses_siembra,
       COALESCE((SELECT array_agg(DISTINCT k.mes ORDER BY k.mes) FROM agro.calendario k WHERE k.cultivo_id = c.id AND k.zona_id IS NULL AND k.fase = 'K'), '{}') AS meses_cosecha,
       (SELECT jsonb_object_agg(f.nombre, a.acciones)
          FROM agro.fases f
          JOIN LATERAL (SELECT jsonb_agg(e.descripcion ORDER BY e.cultivo_id NULLS LAST, e.id) AS acciones
                          FROM agro.acciones_etapa e
                         WHERE e.fase = f.codigo AND (e.cultivo_id = c.id OR e.cultivo_id IS NULL)) a ON a.acciones IS NOT NULL) AS acciones_por_etapa,
       g.codigo AS grupo,
       c.tipo
FROM agro.cultivos c
JOIN agro.grupos_cultivo g ON g.id = c.grupo_id;

-- Calendario de 12 letras por cultivo y piso (lo que usa el frontend)
CREATE OR REPLACE VIEW agro.v_calendario_texto AS
SELECT c.nombre AS cultivo, k.piso, string_agg(k.fase, '' ORDER BY k.mes) AS fases
FROM agro.calendario k JOIN agro.cultivos c ON c.id = k.cultivo_id
WHERE k.zona_id IS NULL
GROUP BY c.nombre, k.piso;
