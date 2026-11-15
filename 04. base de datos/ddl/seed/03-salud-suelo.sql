-- =============================================================================
-- AllpaShift · Salud del suelo: familia botánica, profundidad de raíz y tolerancia a la salinidad
-- de los 37 cultivos. Se puede ejecutar varias veces (también sobre una base ya cargada: es la migración).
--
-- Fuentes:
--   familia              : nombre científico del cultivo (agro.cultivos.nombre_cientifico).
--   profundidad_raiz     : 'profunda' = agro.cultivos.raiz_profunda; el resto según la profundidad radicular
--                          máxima de FAO-56 (Allen et al. 1998, Tabla 22): <= 0,6 m superficial, si no media.
--   tolerancia_salinidad : FAO Riego y Drenaje 29 (Ayers y Westcot 1985, Tabla 4):
--                          sensible = baja, moderadamente sensible = media, moderadamente tolerante o tolerante = alta.
--                          NULL = la tabla no trae el cultivo → "sin dato" (no se aplica la regla).
-- ⚠️ Preliminar, como el resto del catálogo: Alejandro lo valida en feature/catalogo-cultivos.
-- =============================================================================

ALTER TABLE agro.cultivos ADD COLUMN IF NOT EXISTS familia VARCHAR(40);
ALTER TABLE agro.cultivos ADD COLUMN IF NOT EXISTS profundidad_raiz VARCHAR(12)
    CHECK (profundidad_raiz IN ('superficial', 'media', 'profunda'));
ALTER TABLE agro.cultivos ADD COLUMN IF NOT EXISTS tolerancia_salinidad VARCHAR(5)
    CHECK (tolerancia_salinidad IN ('baja', 'media', 'alta'));
ALTER TABLE agro.cultivos ADD COLUMN IF NOT EXISTS es_leguminosa BOOLEAN
    GENERATED ALWAYS AS (familia = 'Fabaceae') STORED;

UPDATE agro.cultivos c
   SET familia = v.familia, profundidad_raiz = v.raiz, tolerancia_salinidad = v.sal
  FROM (VALUES
 -- Cereales
 ('Arroz',              'Poaceae',        'superficial', 'baja'),
 ('Maiz amarillo duro', 'Poaceae',        'media',       'media'),
 ('Maiz amilaceo',      'Poaceae',        'media',       'media'),
 ('Trigo',              'Poaceae',        'media',       'alta'),
 ('Cebada',             'Poaceae',        'media',       'alta'),
 ('Quinua',             'Amaranthaceae',  'media',       NULL),
 -- Menestras (leguminosas)
 ('Frijol caupi',       'Fabaceae',       'media',       'alta'),
 ('Frijol grano seco',  'Fabaceae',       'media',       'baja'),
 ('Arveja grano seco',  'Fabaceae',       'media',       NULL),
 ('Zarandaja',          'Fabaceae',       'profunda',    NULL),
 -- Frutales
 ('Mango',              'Anacardiaceae',  'profunda',    NULL),
 ('Limon',              'Rutaceae',       'profunda',    'baja'),
 ('Uva de mesa',        'Vitaceae',       'profunda',    'media'),
 ('Banano organico',    'Musaceae',       'superficial', NULL),
 ('Platano',            'Musaceae',       'superficial', NULL),
 ('Mandarina',          'Rutaceae',       'profunda',    'baja'),
 ('Palta',              'Lauraceae',      'profunda',    'baja'),
 ('Arandano',           'Ericaceae',      'superficial', NULL),
 ('Maracuya',           'Passifloraceae', 'media',       NULL),
 ('Papaya',             'Caricaceae',     'media',       NULL),
 ('Granadilla',         'Passifloraceae', 'media',       NULL),
 ('Sandia',             'Cucurbitaceae',  'media',       'media'),
 ('Melon',              'Cucurbitaceae',  'media',       'media'),
 -- Hortalizas
 ('Cebolla',            'Amaryllidaceae', 'superficial', 'baja'),
 ('Aji paprika',        'Solanaceae',     'media',       'media'),
 ('Tomate',             'Solanaceae',     'media',       'media'),
 ('Zanahoria',          'Apiaceae',       'media',       'baja'),
 ('Alcachofa',          'Asteraceae',     'profunda',    'alta'),
 ('Esparrago',          'Asparagaceae',   'profunda',    'alta'),
 -- Tubérculos y raíces
 ('Papa',               'Solanaceae',     'superficial', 'media'),
 ('Camote',             'Convolvulaceae', 'media',       'media'),
 ('Yuca',               'Euphorbiaceae',  'profunda',    'media'),
 ('Olluco',             'Basellaceae',    'superficial', NULL),
 -- Industriales
 ('Algodon Pima',       'Malvaceae',      'profunda',    'alta'),
 ('Cana de azucar',     'Poaceae',        'profunda',    'media'),
 ('Cafe',               'Rubiaceae',      'profunda',    NULL),
 ('Cacao',              'Malvaceae',      'profunda',    NULL)
) AS v(nombre, familia, raiz, sal)
 WHERE c.nombre = v.nombre;
