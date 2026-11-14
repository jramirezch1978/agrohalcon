-- Semillas (generado por db/export_postgres.py). Ejecutar desde db/postgres/ con psql.
-- observacion.csv.gz: descomprimir antes (gunzip -k seed/observacion.csv.gz).

\copy region (id, codigo, nombre) FROM 'seed/region.csv' WITH (FORMAT csv, HEADER true)
\copy fuente_dato (id, codigo, nombre, institucion, producto, version, doi, resolucion, cobertura, url, acceso, estado, nota) FROM 'seed/fuente_dato.csv' WITH (FORMAT csv, HEADER true)
\copy variable (id, codigo, nombre, unidad, fuente_id, descripcion) FROM 'seed/variable.csv' WITH (FORMAT csv, HEADER true)
\copy zona (id, nombre, region_id, tipo, lat, lon, aproximada, elevacion_m, pendiente_pct, suelo_ph, suelo_carbono_g_kg, suelo_arcilla_pct, suelo_arena_pct) FROM 'seed/zona.csv' WITH (FORMAT csv, HEADER true)
\copy normal_mensual (zona_id, variable_id, mes, media, desviacion, n_anios, anio_ini, anio_fin) FROM 'seed/normal_mensual.csv' WITH (FORMAT csv, HEADER true)
\copy indice_climatico (codigo, fecha, valor, fuente_id) FROM 'seed/indice_climatico.csv' WITH (FORMAT csv, HEADER true)
\copy episodio_calido (id, indice, inicio, fin, meses, pico_anomalia_c, pico_fecha, media_anomalia_c) FROM 'seed/episodio_calido.csv' WITH (FORMAT csv, HEADER true)
\copy sst_clima (zona_id, doy, media_c, n) FROM 'seed/sst_clima.csv' WITH (FORMAT csv, HEADER true)
\copy tendencia (zona_id, variable_id, anio_ini, anio_fin, metodo, tau, p_valor, pendiente_sen_por_decada, sentido) FROM 'seed/tendencia.csv' WITH (FORMAT csv, HEADER true)
\copy composite_nino (zona_id, variable_id, mes, media_nino, media_normal, razon, n_nino, n_normal) FROM 'seed/composite_nino.csv' WITH (FORMAT csv, HEADER true)
\copy contraste_fuentes (id, par, zona_id, variable, escala, n, periodo_ini, periodo_fin, correlacion, sesgo_medio, rmse, nota) FROM 'seed/contraste_fuentes.csv' WITH (FORMAT csv, HEADER true)
\copy observacion (zona_id, fecha, escala, variable_id, valor, calidad) FROM 'seed/observacion.csv' WITH (FORMAT csv, HEADER true)
\copy validacion_quincena (id, zona_id, evento, desde, hasta, entrada, indicadores, rotaciones, que_hacer, nivel_maximo, advertencias) FROM 'seed/validacion_quincena.csv' WITH (FORMAT csv, HEADER true)
\copy recomendacion_cache (id, zona_id, fecha, payload, creado) FROM 'seed/recomendacion_cache.csv' WITH (FORMAT csv, HEADER true)

SELECT setval(pg_get_serial_sequence('observacion', 'id'), COALESCE((SELECT MAX(id) FROM observacion), 1));
SELECT setval(pg_get_serial_sequence('episodio_calido', 'id'), COALESCE((SELECT MAX(id) FROM episodio_calido), 1));
SELECT setval(pg_get_serial_sequence('validacion_quincena', 'id'), COALESCE((SELECT MAX(id) FROM validacion_quincena), 1));
SELECT setval(pg_get_serial_sequence('recomendacion_cache', 'id'), COALESCE((SELECT MAX(id) FROM recomendacion_cache), 1));
SELECT setval(pg_get_serial_sequence('contraste_fuentes', 'id'), COALESCE((SELECT MAX(id) FROM contraste_fuentes), 1));
