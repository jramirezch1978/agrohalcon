-- AgroShift · esquema PostgreSQL (generado por db/export_postgres.py; no editar a mano)

CREATE TABLE cultivo (
	id INTEGER NOT NULL, 
	nombre VARCHAR(80) NOT NULL, 
	tipo VARCHAR(12) DEFAULT 'anual' NOT NULL, 
	temp_min_c FLOAT NOT NULL, 
	temp_max_c FLOAT NOT NULL, 
	agua_necesaria VARCHAR(6) NOT NULL, 
	meses_siembra JSONB NOT NULL, 
	meses_cosecha JSONB NOT NULL, 
	acciones_por_etapa JSONB, 
	es_prueba BOOLEAN DEFAULT '1' NOT NULL, 
	fuente TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_cultivo_agua CHECK (agua_necesaria IN ('baja','media','alta')), 
	CONSTRAINT ck_cultivo_tipo CHECK (tipo IN ('anual','permanente')), 
	CONSTRAINT ck_cultivo_temp CHECK (temp_min_c < temp_max_c), 
	UNIQUE (nombre)
);

CREATE TABLE episodio_calido (
	id SERIAL NOT NULL, 
	indice VARCHAR(20) NOT NULL, 
	inicio DATE NOT NULL, 
	fin DATE NOT NULL, 
	meses INTEGER NOT NULL, 
	pico_anomalia_c FLOAT NOT NULL, 
	pico_fecha DATE NOT NULL, 
	media_anomalia_c FLOAT NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE fuente_dato (
	id INTEGER NOT NULL, 
	codigo VARCHAR(40) NOT NULL, 
	nombre VARCHAR(120) NOT NULL, 
	institucion VARCHAR(80) NOT NULL, 
	producto VARCHAR(60), 
	version VARCHAR(20), 
	doi VARCHAR(120), 
	resolucion VARCHAR(60), 
	cobertura VARCHAR(60), 
	url VARCHAR(300), 
	acceso VARCHAR(80), 
	estado VARCHAR(20) NOT NULL, 
	nota TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_fuente_estado CHECK (estado IN ('en_uso','probado','bloqueado','planeado')), 
	UNIQUE (codigo)
);

CREATE TABLE region (
	id INTEGER NOT NULL, 
	codigo VARCHAR(30) NOT NULL, 
	nombre VARCHAR(80) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo)
);

CREATE TABLE indice_climatico (
	codigo VARCHAR(20) NOT NULL, 
	fecha DATE NOT NULL, 
	valor FLOAT NOT NULL, 
	fuente_id INTEGER NOT NULL, 
	CONSTRAINT pk_indice_climatico PRIMARY KEY (codigo, fecha), 
	FOREIGN KEY(fuente_id) REFERENCES fuente_dato (id)
);

CREATE TABLE rotacion (
	id INTEGER NOT NULL, 
	nombre VARCHAR(120) NOT NULL, 
	cultivo1_id INTEGER NOT NULL, 
	cultivo2_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_rotacion_par UNIQUE (cultivo1_id, cultivo2_id), 
	FOREIGN KEY(cultivo1_id) REFERENCES cultivo (id), 
	FOREIGN KEY(cultivo2_id) REFERENCES cultivo (id)
);

CREATE TABLE variable (
	id INTEGER NOT NULL, 
	codigo VARCHAR(40) NOT NULL, 
	nombre VARCHAR(120) NOT NULL, 
	unidad VARCHAR(30) NOT NULL, 
	fuente_id INTEGER NOT NULL, 
	descripcion TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (codigo), 
	FOREIGN KEY(fuente_id) REFERENCES fuente_dato (id)
);

CREATE TABLE zona (
	id INTEGER NOT NULL, 
	nombre VARCHAR(120) NOT NULL, 
	region_id INTEGER NOT NULL, 
	tipo VARCHAR(10) DEFAULT 'agricola' NOT NULL, 
	lat FLOAT NOT NULL, 
	lon FLOAT NOT NULL, 
	aproximada BOOLEAN DEFAULT '1' NOT NULL, 
	elevacion_m FLOAT, 
	pendiente_pct FLOAT, 
	suelo_ph FLOAT, 
	suelo_carbono_g_kg FLOAT, 
	suelo_arcilla_pct FLOAT, 
	suelo_arena_pct FLOAT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_zona_tipo CHECK (tipo IN ('agricola','mar','referencia')), 
	CONSTRAINT ck_zona_coord CHECK (lat BETWEEN -90 AND 90 AND lon BETWEEN -180 AND 180), 
	UNIQUE (nombre), 
	FOREIGN KEY(region_id) REFERENCES region (id)
);

CREATE TABLE composite_nino (
	zona_id INTEGER NOT NULL, 
	variable_id INTEGER NOT NULL, 
	mes INTEGER NOT NULL, 
	media_nino FLOAT NOT NULL, 
	media_normal FLOAT NOT NULL, 
	razon FLOAT, 
	n_nino INTEGER NOT NULL, 
	n_normal INTEGER NOT NULL, 
	CONSTRAINT pk_composite_nino PRIMARY KEY (zona_id, variable_id, mes), 
	FOREIGN KEY(zona_id) REFERENCES zona (id), 
	FOREIGN KEY(variable_id) REFERENCES variable (id)
);

CREATE TABLE consulta (
	id SERIAL NOT NULL, 
	lat FLOAT NOT NULL, 
	lon FLOAT NOT NULL, 
	fecha DATE NOT NULL, 
	rotacion_recomendada_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(rotacion_recomendada_id) REFERENCES rotacion (id)
);

CREATE TABLE contraste_fuentes (
	id SERIAL NOT NULL, 
	par VARCHAR(40) NOT NULL, 
	zona_id INTEGER, 
	variable VARCHAR(40) NOT NULL, 
	escala VARCHAR(14) NOT NULL, 
	n INTEGER NOT NULL, 
	periodo_ini DATE NOT NULL, 
	periodo_fin DATE NOT NULL, 
	correlacion FLOAT, 
	sesgo_medio FLOAT, 
	rmse FLOAT, 
	nota TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_contraste UNIQUE (par, zona_id, variable), 
	FOREIGN KEY(zona_id) REFERENCES zona (id)
);

CREATE TABLE normal_mensual (
	zona_id INTEGER NOT NULL, 
	variable_id INTEGER NOT NULL, 
	mes INTEGER NOT NULL, 
	media FLOAT NOT NULL, 
	desviacion FLOAT, 
	n_anios INTEGER NOT NULL, 
	anio_ini INTEGER NOT NULL, 
	anio_fin INTEGER NOT NULL, 
	CONSTRAINT pk_normal_mensual PRIMARY KEY (zona_id, variable_id, mes), 
	CONSTRAINT ck_normal_mes CHECK (mes BETWEEN 1 AND 12), 
	FOREIGN KEY(zona_id) REFERENCES zona (id), 
	FOREIGN KEY(variable_id) REFERENCES variable (id)
);

CREATE TABLE observacion (
	id BIGSERIAL NOT NULL, 
	zona_id INTEGER NOT NULL, 
	fecha DATE NOT NULL, 
	escala VARCHAR(14) NOT NULL, 
	variable_id INTEGER NOT NULL, 
	valor FLOAT NOT NULL, 
	calidad VARCHAR(30), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_observacion UNIQUE (zona_id, fecha, escala, variable_id), 
	CONSTRAINT ck_obs_escala CHECK (escala IN ('diaria','mensual','compuesta16d')), 
	FOREIGN KEY(zona_id) REFERENCES zona (id), 
	FOREIGN KEY(variable_id) REFERENCES variable (id)
);

CREATE INDEX ix_obs_zona_var_fecha ON observacion (zona_id, variable_id, fecha);

CREATE TABLE recomendacion_cache (
	id SERIAL NOT NULL, 
	zona_id INTEGER NOT NULL, 
	fecha DATE NOT NULL, 
	payload JSONB NOT NULL, 
	creado TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_reco_cache UNIQUE (zona_id, fecha), 
	FOREIGN KEY(zona_id) REFERENCES zona (id)
);

CREATE TABLE sst_clima (
	zona_id INTEGER NOT NULL, 
	doy INTEGER NOT NULL, 
	media_c FLOAT NOT NULL, 
	n INTEGER NOT NULL, 
	CONSTRAINT pk_sst_clima PRIMARY KEY (zona_id, doy), 
	FOREIGN KEY(zona_id) REFERENCES zona (id)
);

CREATE TABLE tendencia (
	zona_id INTEGER NOT NULL, 
	variable_id INTEGER NOT NULL, 
	anio_ini INTEGER NOT NULL, 
	anio_fin INTEGER NOT NULL, 
	metodo VARCHAR(40) NOT NULL, 
	tau FLOAT, 
	p_valor FLOAT, 
	pendiente_sen_por_decada FLOAT, 
	sentido VARCHAR(20) NOT NULL, 
	CONSTRAINT pk_tendencia PRIMARY KEY (zona_id, variable_id, metodo), 
	FOREIGN KEY(zona_id) REFERENCES zona (id), 
	FOREIGN KEY(variable_id) REFERENCES variable (id)
);

CREATE TABLE validacion_quincena (
	id SERIAL NOT NULL, 
	zona_id INTEGER NOT NULL, 
	evento VARCHAR(40) NOT NULL, 
	desde DATE NOT NULL, 
	hasta DATE NOT NULL, 
	entrada JSONB NOT NULL, 
	indicadores JSONB NOT NULL, 
	rotaciones JSONB, 
	que_hacer JSONB, 
	nivel_maximo VARCHAR(5) NOT NULL, 
	advertencias JSONB, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_validacion UNIQUE (zona_id, evento, hasta), 
	CONSTRAINT ck_validacion_nivel CHECK (nivel_maximo IN ('bajo','medio','alto')), 
	FOREIGN KEY(zona_id) REFERENCES zona (id)
);

CREATE OR REPLACE VIEW v_datos_nasa AS SELECT o.id, z.lat, z.lon, o.fecha, f.nombre AS fuente, v.codigo AS variable, o.valor FROM observacion o JOIN zona z ON z.id = o.zona_id JOIN variable v ON v.id = o.variable_id JOIN fuente_dato f ON f.id = v.fuente_id;

CREATE OR REPLACE VIEW v_anomalia_mensual AS SELECT o.zona_id, o.variable_id, o.fecha, o.valor, n.media AS normal, n.desviacion, o.valor - n.media AS anomalia, (o.valor - n.media) / NULLIF(n.desviacion, 0) AS z FROM observacion o JOIN normal_mensual n ON n.zona_id = o.zona_id AND n.variable_id = o.variable_id AND n.mes = CAST(SUBSTR(CAST(o.fecha AS VARCHAR(10)), 6, 2) AS INTEGER) WHERE o.escala = 'mensual';

CREATE OR REPLACE VIEW v_ultimo_dato AS SELECT zona_id, variable_id, fecha, valor, escala FROM ( SELECT o.zona_id, o.variable_id, o.fecha, o.valor, o.escala, ROW_NUMBER() OVER (PARTITION BY o.zona_id, o.variable_id ORDER BY o.fecha DESC) AS rn FROM observacion o ) t WHERE rn = 1;

CREATE OR REPLACE VIEW v_validacion_resumen AS SELECT z.nombre AS zona, v.evento, v.desde, v.hasta, v.nivel_maximo FROM validacion_quincena v JOIN zona z ON z.id = v.zona_id;
