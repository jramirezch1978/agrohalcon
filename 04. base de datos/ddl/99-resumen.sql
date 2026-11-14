-- Resumen del despliegue de base de datos (modelo v2)
SELECT 'agro.regiones' AS tabla, count(*) AS filas FROM agro.regiones
UNION ALL SELECT 'agro.zonas',             count(*) FROM agro.zonas
UNION ALL SELECT 'agro.grupos_cultivo',    count(*) FROM agro.grupos_cultivo
UNION ALL SELECT 'agro.cultivos',          count(*) FROM agro.cultivos
UNION ALL SELECT 'agro.cultivos_zona',     count(*) FROM agro.cultivos_zona
UNION ALL SELECT 'agro.superficie_region', count(*) FROM agro.superficie_region
UNION ALL SELECT 'agro.calendario',        count(*) FROM agro.calendario
UNION ALL SELECT 'agro.acciones_etapa',    count(*) FROM agro.acciones_etapa
UNION ALL SELECT 'agro.rotaciones',        count(*) FROM agro.rotaciones
UNION ALL SELECT 'agro.parcelas',          count(*) FROM agro.parcelas
UNION ALL SELECT 'agro.consultas',         count(*) FROM agro.consultas
UNION ALL SELECT 'agro.riesgo_mensual',    count(*) FROM agro.riesgo_mensual
UNION ALL SELECT 'nasa.datasets',          count(*) FROM nasa.datasets
UNION ALL SELECT 'nasa.datos_nasa',        count(*) FROM nasa.datos_nasa
UNION ALL SELECT 'nasa.eventos_enso',      count(*) FROM nasa.eventos_enso
UNION ALL SELECT 'ref.referencias',        count(*) FROM ref.referencias;
