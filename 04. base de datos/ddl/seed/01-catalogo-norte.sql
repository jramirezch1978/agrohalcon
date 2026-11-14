-- ============================================================================
-- AllpaShift - Seed del catalogo del norte del Peru (v2, 2026-11-14)
-- PRELIMINAR: calendarios y Kc aproximados (FAO-56, MIDAGRI, DRAP Piura). Alejandro valida.
-- Idempotente: se puede ejecutar varias veces.
-- ============================================================================
SET client_min_messages = warning;

-- 1. Regiones -----------------------------------------------------------------
INSERT INTO agro.regiones (codigo, nombre, lat, lon) VALUES
 ('tumbes', 'Tumbes', -3.566, -80.451), ('piura', 'Piura', -5.194, -80.632),
 ('lambayeque', 'Lambayeque', -6.701, -79.906), ('la_libertad', 'La Libertad', -8.111, -79.029),
 ('cajamarca', 'Cajamarca', -7.163, -78.500), ('amazonas', 'Amazonas', -6.231, -77.869),
 ('san_martin', 'San Martin', -6.034, -76.971)
ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre, lat = EXCLUDED.lat, lon = EXCLUDED.lon;

-- 2. Zonas / valles (mismos 16 de David: data/backup/zonas_seed.sql) + Huarmaca y Ayabaca ----
INSERT INTO agro.zonas (id, nombre, lat, lon, region, piso, cuenca, fuente) VALUES
 (1,  'Bajo Piura',                -5.35,  -80.70, 'piura',       'costa',  'Piura',   'David (aprox.)'),
 (2,  'Valle del Chira',           -4.90,  -80.85, 'piura',       'costa',  'Chira',   'David (aprox.)'),
 (3,  'Medio Piura - Castilla',    -5.20,  -80.62, 'piura',       'costa',  'Piura',   'David (aprox.)'),
 (4,  'San Lorenzo - Tambogrande', -4.93,  -80.34, 'piura',       'costa',  'Piura',   'David (aprox.)'),
 (5,  'Alto Piura - Chulucanas',   -5.10,  -80.16, 'piura',       'costa',  'Piura',   'David (aprox.)'),
 (6,  'Sechura - Bernal / Vice',   -5.45,  -80.80, 'piura',       'costa',  'Piura',   'David (aprox.)'),
 (7,  'Sierra - Huancabamba',      -5.24,  -79.45, 'piura',       'sierra', 'Huancabamba', 'David (aprox.)'),
 (8,  'Valle de Tumbes',           -3.57,  -80.45, 'tumbes',      'costa',  'Tumbes',  'David (aprox.)'),
 (9,  'Chancay-Lambayeque',        -6.70,  -79.90, 'lambayeque',  'costa',  'Chancay-Lambayeque', 'David (aprox.)'),
 (10, 'Olmos',                     -5.99,  -79.74, 'lambayeque',  'costa',  'Olmos',   'David (aprox.)'),
 (11, 'Jequetepeque',              -7.20,  -79.45, 'la_libertad', 'costa',  'Jequetepeque', 'David (aprox.)'),
 (12, 'Chavimochic - Viru',        -8.41,  -78.75, 'la_libertad', 'costa',  'Viru-Chao', 'David (aprox.)'),
 (13, 'Jaen',                      -5.71,  -78.81, 'cajamarca',   'selva',  'Chinchipe', 'David (aprox.)'),
 (14, 'Valle de Cajamarca',        -7.16,  -78.50, 'cajamarca',   'sierra', 'Cajamarca', 'David (aprox.)'),
 (15, 'Bagua - Utcubamba',         -5.64,  -78.53, 'amazonas',    'selva',  'Utcubamba', 'David (aprox.)'),
 (16, 'Alto Mayo - Moyobamba',     -6.03,  -76.97, 'san_martin',  'selva',  'Mayo',    'David (aprox.)'),
 (17, 'Sierra - Huarmaca',         -5.57,  -79.52, 'piura',       'sierra', 'Huancabamba', 'Jhonny (aprox.)'),
 (18, 'Sierra - Ayabaca',          -4.64,  -79.71, 'piura',       'sierra', 'Chira-Quiroz', 'Jhonny (aprox.)')
ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
  region = EXCLUDED.region, piso = EXCLUDED.piso, cuenca = EXCLUDED.cuenca;
SELECT setval('agro.zonas_id_seq', (SELECT max(id) FROM agro.zonas));

-- 3. Grupos y fases -----------------------------------------------------------
INSERT INTO agro.grupos_cultivo (codigo, nombre) VALUES
 ('cereal', 'Cereales'), ('menestra', 'Menestras'), ('frutal', 'Frutales'),
 ('hortaliza', 'Hortalizas'), ('tuberculo', 'Tuberculos y raices'), ('industrial', 'Industriales')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO agro.fases (codigo, nombre) VALUES
 ('S', 'Siembra'), ('C', 'Crecimiento'), ('F', 'Floracion'), ('K', 'Cosecha'), ('D', 'Descanso / poda')
ON CONFLICT (codigo) DO NOTHING;

-- 4. Cultivos (Kc FAO-56 aproximados; agua = mm por campana o por ano en permanentes) ----
INSERT INTO agro.cultivos (nombre, nombre_cientifico, grupo_id, tipo, temp_min_c, temp_max_c, agua_necesaria, agua_mm_min, agua_mm_max,
                           ciclo_dias, kc_inicial, kc_medio, kc_final, fija_nitrogeno, cultivo_cobertura, raiz_profunda, tolera_sequia, tolera_inundacion, fuente)
SELECT v.nombre, v.cientifico, g.id, v.tipo, v.tmin, v.tmax, v.agua, v.amin, v.amax, v.ciclo, v.kci, v.kcm, v.kcf, v.fn, v.cob, v.raiz, v.seq, v.inu, v.fuente
FROM (VALUES
 -- Cereales
 ('Arroz',                'Oryza sativa',          'cereal',     'anual',          20, 35, 'alta',  1200, 2000, 150, 1.05, 1.20, 0.90, FALSE, FALSE, FALSE, FALSE, TRUE,  'FAO-56; DRAP Piura 2025-26: 54 424 ha'),
 ('Maiz amarillo duro',   'Zea mays',              'cereal',     'anual',          16, 32, 'media',  500,  800, 130, 0.30, 1.20, 0.60, FALSE, FALSE, FALSE, FALSE, FALSE, 'FAO-56; DRAP Piura: 25 430 ha'),
 ('Maiz amilaceo',        'Zea mays (amylacea)',   'cereal',     'anual',          10, 26, 'media',  450,  700, 180, 0.30, 1.15, 0.60, FALSE, FALSE, FALSE, FALSE, FALSE, 'FAO-56; DRAP Piura: 12 473 ha (sierra)'),
 ('Trigo',                'Triticum aestivum',     'cereal',     'anual',           5, 25, 'media',  400,  600, 150, 0.40, 1.15, 0.30, FALSE, FALSE, FALSE, TRUE,  FALSE, 'FAO-56; DRAP Piura: 4 769 ha (sierra)'),
 ('Cebada',               'Hordeum vulgare',       'cereal',     'anual',           4, 24, 'baja',   350,  550, 140, 0.30, 1.15, 0.25, FALSE, FALSE, FALSE, TRUE,  FALSE, 'FAO-56; sierra de Piura y Cajamarca'),
 ('Quinua',               'Chenopodium quinoa',    'cereal',     'anual',           5, 28, 'baja',   300,  500, 150, 0.50, 1.00, 0.70, FALSE, FALSE, FALSE, TRUE,  FALSE, 'FAO; Huancabamba'),
 -- Menestras
 ('Frijol caupi',         'Vigna unguiculata',     'menestra',   'anual',          18, 35, 'baja',   300,  500,  90, 0.40, 1.05, 0.60, TRUE,  TRUE,  FALSE, TRUE,  FALSE, 'FAO-56; DRAP Piura: 8 658 ha (frijol Castilla)'),
 ('Frijol grano seco',    'Phaseolus vulgaris',    'menestra',   'anual',          12, 30, 'media',  350,  500, 100, 0.40, 1.15, 0.35, TRUE,  TRUE,  FALSE, FALSE, FALSE, 'FAO-56; DRAP Piura: 6 593 ha'),
 ('Arveja grano seco',    'Pisum sativum',         'menestra',   'anual',           7, 24, 'media',  350,  500, 120, 0.50, 1.15, 0.30, TRUE,  TRUE,  FALSE, FALSE, FALSE, 'FAO-56; DRAP Piura: 3 859 ha (sierra)'),
 ('Zarandaja',            'Lablab purpureus',      'menestra',   'anual',          18, 34, 'baja',   300,  450, 120, 0.40, 1.05, 0.60, TRUE,  TRUE,  TRUE,  TRUE,  FALSE, 'Bajo Piura (menestra tipica)'),
 -- Frutales
 ('Mango',                'Mangifera indica',      'frutal',     'permanente',     20, 36, 'media',  800, 1200, NULL, 0.60, 0.85, 0.75, FALSE, FALSE, TRUE,  TRUE,  FALSE, 'FAO-56 aprox.; 3.er cultivo de Piura (BCRP)'),
 ('Limon',                'Citrus aurantiifolia',  'frutal',     'permanente',     18, 34, 'media',  900, 1200, NULL, 0.70, 0.65, 0.70, FALSE, FALSE, TRUE,  FALSE, FALSE, 'FAO-56 citricos; Piura ~63 % de la produccion nacional'),
 ('Uva de mesa',          'Vitis vinifera',        'frutal',     'permanente',     15, 35, 'media',  500,  900, NULL, 0.30, 0.85, 0.45, FALSE, FALSE, TRUE,  TRUE,  FALSE, 'FAO-56; Piura primer exportador (cosecha oct-ene)'),
 ('Banano organico',      'Musa AAA',              'frutal',     'permanente',     20, 35, 'alta',  1200, 2200, NULL, 0.50, 1.10, 1.00, FALSE, FALSE, FALSE, FALSE, FALSE, 'FAO-56; Chira, Tumbes, Alto Piura'),
 ('Platano',              'Musa AAB',              'frutal',     'permanente',     20, 35, 'alta',  1200, 2000, NULL, 0.50, 1.10, 1.00, FALSE, FALSE, FALSE, FALSE, FALSE, 'FAO-56; 5.o cultivo de Piura (BCRP)'),
 ('Mandarina',            'Citrus reticulata',     'frutal',     'permanente',     13, 35, 'media',  900, 1200, NULL, 0.65, 0.60, 0.65, FALSE, FALSE, TRUE,  FALSE, FALSE, 'FAO-56 citricos; cosecha feb-set (MIDAGRI)'),
 ('Palta',                'Persea americana',      'frutal',     'permanente',     15, 30, 'alta',  1000, 1400, NULL, 0.60, 0.85, 0.75, FALSE, FALSE, TRUE,  FALSE, FALSE, 'FAO-56 palto'),
 ('Arandano',             'Vaccinium corymbosum',  'frutal',     'permanente',     10, 30, 'media',  600, 1000, NULL, 0.30, 1.05, 0.50, FALSE, FALSE, FALSE, FALSE, FALSE, 'FAO-56 berries'),
 ('Maracuya',             'Passiflora edulis',     'frutal',     'semipermanente', 18, 32, 'media',  800, 1500, NULL, 0.50, 0.90, 0.80, FALSE, FALSE, FALSE, FALSE, FALSE, 'Kc aprox.; Lambayeque, Piura'),
 ('Papaya',               'Carica papaya',         'frutal',     'semipermanente', 20, 34, 'alta',  1000, 1500, NULL, 0.60, 1.00, 0.90, FALSE, FALSE, FALSE, FALSE, FALSE, 'Kc aprox.; Piura'),
 ('Granadilla',           'Passiflora ligularis',  'frutal',     'semipermanente', 12, 24, 'media',  800, 1200, NULL, 0.50, 0.90, 0.80, FALSE, FALSE, FALSE, FALSE, FALSE, 'Kc aprox.; sierra de Piura'),
 ('Sandia',               'Citrullus lanatus',     'hortaliza',  'anual',          18, 35, 'media',  400,  600,  90, 0.40, 1.00, 0.75, FALSE, TRUE,  FALSE, FALSE, FALSE, 'FAO-56; piloto en Piura en lugar de banano (Fusarium, 2026)'),
 ('Melon',                'Cucumis melo',          'hortaliza',  'anual',          18, 35, 'media',  400,  600,  90, 0.50, 1.05, 0.75, FALSE, TRUE,  FALSE, FALSE, FALSE, 'FAO-56'),
 -- Hortalizas
 ('Cebolla',              'Allium cepa',           'hortaliza',  'anual',          10, 30, 'media',  350,  550, 150, 0.70, 1.05, 0.75, FALSE, FALSE, FALSE, FALSE, FALSE, 'FAO-56; DRAP Piura hortalizas'),
 ('Aji paprika',          'Capsicum annuum',       'hortaliza',  'anual',          15, 32, 'media',  500,  700, 180, 0.60, 1.05, 0.90, FALSE, FALSE, FALSE, FALSE, FALSE, 'FAO-56 pimiento; DRAP Piura hortalizas'),
 ('Tomate',               'Solanum lycopersicum',  'hortaliza',  'anual',          15, 32, 'media',  400,  600, 130, 0.60, 1.15, 0.80, FALSE, FALSE, FALSE, FALSE, FALSE, 'FAO-56; DRAP Piura hortalizas'),
 ('Zanahoria',            'Daucus carota',         'hortaliza',  'anual',           8, 28, 'media',  350,  500, 110, 0.70, 1.05, 0.95, FALSE, FALSE, FALSE, FALSE, FALSE, 'FAO-56; DRAP Piura hortalizas'),
 ('Alcachofa',            'Cynara scolymus',       'hortaliza',  'semipermanente', 7, 28, 'media',  600,  900, NULL, 0.50, 1.00, 0.95, FALSE, FALSE, TRUE,  FALSE, FALSE, 'FAO-56; La Libertad (no figura en DRAP Piura)'),
 ('Esparrago',            'Asparagus officinalis', 'hortaliza',  'permanente',     10, 30, 'media',  900, 1300, NULL, 0.50, 0.95, 0.30, FALSE, FALSE, TRUE,  TRUE,  FALSE, 'FAO-56; La Libertad'),
 -- Tuberculos y raices
 ('Papa',                 'Solanum tuberosum',     'tuberculo',  'anual',           7, 24, 'media',  500,  700, 150, 0.50, 1.15, 0.75, FALSE, FALSE, FALSE, FALSE, FALSE, 'FAO-56; sierra'),
 ('Camote',               'Ipomoea batatas',       'tuberculo',  'anual',          15, 33, 'baja',   400,  600, 130, 0.50, 1.15, 0.65, FALSE, TRUE,  FALSE, TRUE,  FALSE, 'FAO-56; DRAP Piura tuberculos'),
 ('Yuca',                 'Manihot esculenta',     'tuberculo',  'anual',          18, 35, 'baja',   500, 1000, 300, 0.30, 0.80, 0.30, FALSE, FALSE, TRUE,  TRUE,  FALSE, 'FAO-56; DRAP Piura tuberculos'),
 ('Olluco',               'Ullucus tuberosus',     'tuberculo',  'anual',           5, 20, 'media',  500,  700, 180, 0.50, 1.05, 0.70, FALSE, FALSE, FALSE, FALSE, FALSE, 'Kc aprox.; sierra de Piura'),
 -- Industriales
 ('Algodon Pima',         'Gossypium barbadense',  'industrial', 'anual',          18, 35, 'media',  700, 1300, 210, 0.35, 1.15, 0.70, FALSE, FALSE, TRUE,  TRUE,  FALSE, 'FAO-56; DRAP Piura: 2 091 ha (Bajo Piura)'),
 ('Cana de azucar',       'Saccharum officinarum', 'industrial', 'permanente',     20, 35, 'alta',  1500, 2500, NULL, 0.40, 1.25, 0.75, FALSE, FALSE, TRUE,  FALSE, FALSE, 'FAO-56; Chira (etanol), Lambayeque, La Libertad'),
 ('Cafe',                 'Coffea arabica',        'industrial', 'permanente',     15, 28, 'alta',  1200, 1800, NULL, 0.90, 0.95, 0.95, FALSE, FALSE, TRUE,  FALSE, FALSE, 'FAO-56; Huancabamba, Ayabaca, Jaen'),
 ('Cacao',                'Theobroma cacao',       'industrial', 'permanente',     18, 32, 'alta',  1500, 2500, NULL, 1.00, 1.05, 1.05, FALSE, FALSE, TRUE,  FALSE, FALSE, 'FAO-56; Alto Piura, Amazonas, San Martin')
) AS v(nombre, cientifico, grupo, tipo, tmin, tmax, agua, amin, amax, ciclo, kci, kcm, kcf, fn, cob, raiz, seq, inu, fuente)
JOIN agro.grupos_cultivo g ON g.codigo = v.grupo
ON CONFLICT (nombre) DO UPDATE SET nombre_cientifico = EXCLUDED.nombre_cientifico, grupo_id = EXCLUDED.grupo_id, tipo = EXCLUDED.tipo,
  temp_min_c = EXCLUDED.temp_min_c, temp_max_c = EXCLUDED.temp_max_c, agua_necesaria = EXCLUDED.agua_necesaria,
  agua_mm_min = EXCLUDED.agua_mm_min, agua_mm_max = EXCLUDED.agua_mm_max, ciclo_dias = EXCLUDED.ciclo_dias,
  kc_inicial = EXCLUDED.kc_inicial, kc_medio = EXCLUDED.kc_medio, kc_final = EXCLUDED.kc_final,
  fija_nitrogeno = EXCLUDED.fija_nitrogeno, cultivo_cobertura = EXCLUDED.cultivo_cobertura, raiz_profunda = EXCLUDED.raiz_profunda,
  tolera_sequia = EXCLUDED.tolera_sequia, tolera_inundacion = EXCLUDED.tolera_inundacion, fuente = EXCLUDED.fuente;

-- 5. Calendario general por piso (12 letras ene..dic: S siembra, C crecimiento, F floracion, K cosecha, D descanso/poda)
INSERT INTO agro.calendario (cultivo_id, piso, zona_id, mes, fase)
SELECT c.id, cal.piso, NULL, m.mes, substr(cal.fases, m.mes, 1)
FROM (VALUES
  ('Arroz','costa','SCCCKKDDDDDS'), ('Arroz','selva','CCKKSSCCKKSS'),
  ('Maiz amarillo duro','costa','SCCKKSCCKKSC'), ('Maiz amilaceo','sierra','CCFCKKDDDSSC'),
  ('Trigo','sierra','SSCCFKKDDDDS'), ('Cebada','sierra','SSCCFKKDDDDS'), ('Quinua','sierra','CCCFKKDDDDSS'),
  ('Frijol caupi','costa','CKKSSCCKKDDS'), ('Frijol grano seco','costa','DDDDSSCCKKDD'),
  ('Arveja grano seco','sierra','SSCFKKDDDDDS'), ('Zarandaja','costa','DDDSSCCKKKDD'),
  ('Mango','costa','KKKDDCFFFCKK'), ('Limon','costa','KKKKKCCFFCCK'), ('Uva de mesa','costa','KDDDDDCFCKKK'),
  ('Banano organico','costa','KKKKKKKKKKKK'), ('Platano','costa','KKKKKKKKKKKK'), ('Platano','selva','KKKKKKKKKKKK'),
  ('Mandarina','costa','CCKKKKKKFFCC'), ('Palta','costa','CCKKKKCFFCCC'), ('Arandano','costa','CCCCFFKKKKKC'),
  ('Maracuya','costa','KKKKCCFCCKKK'), ('Papaya','costa','KKKKKKKKKKKK'), ('Granadilla','sierra','CCKKKKKKCFFC'),
  ('Sandia','costa','DDDDDSSCKKKD'), ('Melon','costa','DDDDDSSCKKKD'),
  ('Cebolla','costa','DDDSSSCCKKKD'), ('Aji paprika','costa','DDSSSCCKKKDD'), ('Tomate','costa','DDSSCCKKKDDD'),
  ('Zanahoria','costa','DDSSCCKKDDDD'), ('Alcachofa','costa','DDSSCCCFKKKK'), ('Esparrago','costa','KKKKCCKKKKKK'),
  ('Papa','sierra','CCFKKKDDDSSS'), ('Camote','costa','DDDSSCCKKDDD'), ('Yuca','costa','CKKKDDSSCCCC'), ('Olluco','sierra','CCKKKDDDSSSC'),
  ('Algodon Pima','costa','DSSCCCFFKKKD'), ('Cana de azucar','costa','KKKKKKKKKKKK'),
  ('Cafe','sierra','CCFKKKKKCFCC'), ('Cafe','selva','CCFKKKKKCFCC'), ('Cacao','costa','CCKKKKCCCFFC'), ('Cacao','selva','CCKKKKCCCFFC')
) AS cal(cultivo, piso, fases)
JOIN agro.cultivos c ON c.nombre = cal.cultivo
CROSS JOIN generate_series(1, 12) AS m(mes)
ON CONFLICT (cultivo_id, piso, zona_id, mes) DO UPDATE SET fase = EXCLUDED.fase;

-- 6. Cultivos por zona (principales) ------------------------------------------
INSERT INTO agro.cultivos_zona (cultivo_id, zona_id, campania, superficie_ha, principal, fuente)
SELECT c.id, z.id, '2025-2026', v.ha, v.principal, v.fuente
FROM (VALUES
  -- Arroz: desglose DRAP Piura 2025-2026
  ('Arroz', 'Bajo Piura', 9259.0, TRUE, 'DRAP Piura: 18 518 ha Medio y Bajo Piura (repartido 50/50)'),
  ('Arroz', 'Medio Piura - Castilla', 9259.0, TRUE, 'DRAP Piura: 18 518 ha Medio y Bajo Piura (repartido 50/50)'),
  ('Arroz', 'Alto Piura - Chulucanas', 3716.0, TRUE, 'DRAP Piura 2025-2026'),
  ('Arroz', 'San Lorenzo - Tambogrande', 9004.0, TRUE, 'DRAP Piura 2025-2026'),
  ('Arroz', 'Valle del Chira', 22554.0, TRUE, 'DRAP Piura 2025-2026'),
  ('Arroz', 'Sierra - Huancabamba', 168.0, FALSE, 'DRAP Piura 2025-2026'),
  ('Arroz', 'Sierra - Huarmaca', 360.0, FALSE, 'DRAP Piura 2025-2026'),
  ('Arroz', 'Sierra - Ayabaca', 59.0, FALSE, 'DRAP Piura 2025-2026'),
  ('Algodon Pima', 'Bajo Piura', NULL, TRUE, 'DRAP Piura: mayor parte de 2 091 ha'),
  ('Limon', 'San Lorenzo - Tambogrande', NULL, TRUE, 'Valle de San Lorenzo (limon)'), ('Limon', 'Alto Piura - Chulucanas', NULL, TRUE, NULL),
  ('Limon', 'Valle del Chira', NULL, FALSE, NULL), ('Limon', 'Valle de Tumbes', NULL, FALSE, NULL), ('Limon', 'Chancay-Lambayeque', NULL, FALSE, NULL),
  ('Mango', 'San Lorenzo - Tambogrande', NULL, TRUE, NULL), ('Mango', 'Alto Piura - Chulucanas', NULL, TRUE, NULL), ('Mango', 'Valle del Chira', NULL, FALSE, NULL),
  ('Mango', 'Olmos', NULL, TRUE, 'Motupe-Olmos'), ('Mango', 'Chancay-Lambayeque', NULL, FALSE, NULL),
  ('Uva de mesa', 'Medio Piura - Castilla', NULL, TRUE, NULL), ('Uva de mesa', 'Bajo Piura', NULL, FALSE, NULL), ('Uva de mesa', 'Valle del Chira', NULL, TRUE, NULL),
  ('Uva de mesa', 'San Lorenzo - Tambogrande', NULL, FALSE, NULL), ('Uva de mesa', 'Olmos', NULL, TRUE, NULL), ('Uva de mesa', 'Chavimochic - Viru', NULL, TRUE, NULL),
  ('Banano organico', 'Valle del Chira', NULL, TRUE, 'Querecotillo, Salitral'), ('Banano organico', 'Valle de Tumbes', NULL, TRUE, NULL), ('Banano organico', 'Alto Piura - Chulucanas', NULL, FALSE, NULL),
  ('Platano', 'Alto Piura - Chulucanas', NULL, TRUE, NULL), ('Platano', 'San Lorenzo - Tambogrande', NULL, TRUE, NULL), ('Platano', 'Alto Mayo - Moyobamba', NULL, TRUE, NULL), ('Platano', 'Bagua - Utcubamba', NULL, TRUE, NULL),
  ('Mandarina', 'Medio Piura - Castilla', NULL, FALSE, 'Secundario en el norte'), ('Mandarina', 'Chancay-Lambayeque', NULL, FALSE, NULL), ('Mandarina', 'Chavimochic - Viru', NULL, FALSE, NULL),
  ('Palta', 'Olmos', NULL, TRUE, NULL), ('Palta', 'Chavimochic - Viru', NULL, TRUE, NULL), ('Palta', 'Valle del Chira', NULL, FALSE, NULL),
  ('Arandano', 'Chavimochic - Viru', NULL, TRUE, NULL), ('Arandano', 'Olmos', NULL, TRUE, NULL), ('Arandano', 'Medio Piura - Castilla', NULL, FALSE, NULL),
  ('Maracuya', 'Chancay-Lambayeque', NULL, TRUE, NULL), ('Maracuya', 'Alto Piura - Chulucanas', NULL, FALSE, NULL),
  ('Papaya', 'Alto Piura - Chulucanas', NULL, FALSE, NULL), ('Granadilla', 'Sierra - Ayabaca', NULL, FALSE, NULL), ('Granadilla', 'Sierra - Huancabamba', NULL, FALSE, NULL),
  ('Sandia', 'Valle del Chira', NULL, FALSE, 'Piloto 2026 (Fusarium en banano)'), ('Sandia', 'Bajo Piura', NULL, FALSE, NULL), ('Melon', 'Bajo Piura', NULL, FALSE, NULL),
  ('Maiz amarillo duro', 'Bajo Piura', NULL, TRUE, NULL), ('Maiz amarillo duro', 'Medio Piura - Castilla', NULL, TRUE, NULL), ('Maiz amarillo duro', 'Alto Piura - Chulucanas', NULL, TRUE, NULL),
  ('Maiz amarillo duro', 'Chancay-Lambayeque', NULL, TRUE, NULL), ('Maiz amarillo duro', 'Alto Mayo - Moyobamba', NULL, FALSE, NULL),
  ('Frijol caupi', 'Bajo Piura', NULL, TRUE, NULL), ('Frijol caupi', 'Sechura - Bernal / Vice', NULL, TRUE, NULL), ('Frijol caupi', 'Chancay-Lambayeque', NULL, FALSE, NULL),
  ('Zarandaja', 'Bajo Piura', NULL, TRUE, NULL), ('Zarandaja', 'Sechura - Bernal / Vice', NULL, TRUE, NULL),
  ('Frijol grano seco', 'Alto Piura - Chulucanas', NULL, FALSE, NULL),
  ('Cebolla', 'Bajo Piura', NULL, FALSE, NULL), ('Aji paprika', 'Bajo Piura', NULL, FALSE, NULL), ('Aji paprika', 'Sechura - Bernal / Vice', NULL, FALSE, NULL),
  ('Tomate', 'Medio Piura - Castilla', NULL, FALSE, NULL), ('Zanahoria', 'Sierra - Huancabamba', NULL, FALSE, NULL),
  ('Camote', 'Bajo Piura', NULL, FALSE, NULL), ('Camote', 'Sechura - Bernal / Vice', NULL, FALSE, NULL), ('Yuca', 'Alto Piura - Chulucanas', NULL, FALSE, NULL), ('Yuca', 'Sechura - Bernal / Vice', NULL, FALSE, NULL),
  ('Alcachofa', 'Chavimochic - Viru', NULL, TRUE, NULL), ('Esparrago', 'Chavimochic - Viru', NULL, TRUE, NULL),
  ('Cana de azucar', 'Valle del Chira', NULL, TRUE, 'Etanol'), ('Cana de azucar', 'Chancay-Lambayeque', NULL, TRUE, NULL), ('Cana de azucar', 'Chavimochic - Viru', NULL, TRUE, NULL),
  ('Papa', 'Sierra - Huancabamba', NULL, TRUE, NULL), ('Papa', 'Sierra - Ayabaca', NULL, TRUE, NULL), ('Papa', 'Valle de Cajamarca', NULL, TRUE, NULL),
  ('Maiz amilaceo', 'Sierra - Huancabamba', NULL, TRUE, NULL), ('Maiz amilaceo', 'Sierra - Ayabaca', NULL, TRUE, NULL), ('Maiz amilaceo', 'Sierra - Huarmaca', NULL, TRUE, NULL), ('Maiz amilaceo', 'Valle de Cajamarca', NULL, TRUE, NULL),
  ('Trigo', 'Sierra - Huancabamba', NULL, TRUE, NULL), ('Trigo', 'Sierra - Ayabaca', NULL, TRUE, NULL), ('Trigo', 'Valle de Cajamarca', NULL, TRUE, NULL),
  ('Cebada', 'Sierra - Huancabamba', NULL, TRUE, NULL), ('Cebada', 'Valle de Cajamarca', NULL, TRUE, NULL),
  ('Arveja grano seco', 'Sierra - Huancabamba', NULL, TRUE, NULL), ('Arveja grano seco', 'Sierra - Ayabaca', NULL, FALSE, NULL),
  ('Quinua', 'Sierra - Huancabamba', NULL, FALSE, NULL), ('Olluco', 'Sierra - Ayabaca', NULL, FALSE, NULL), ('Olluco', 'Sierra - Huancabamba', NULL, FALSE, NULL),
  ('Cafe', 'Sierra - Huancabamba', NULL, TRUE, NULL), ('Cafe', 'Sierra - Ayabaca', NULL, TRUE, NULL), ('Cafe', 'Jaen', NULL, TRUE, NULL), ('Cafe', 'Alto Mayo - Moyobamba', NULL, TRUE, NULL),
  ('Cacao', 'Alto Piura - Chulucanas', NULL, FALSE, NULL), ('Cacao', 'Bagua - Utcubamba', NULL, TRUE, NULL), ('Cacao', 'Alto Mayo - Moyobamba', NULL, TRUE, NULL),
  ('Arroz', 'Valle de Tumbes', NULL, TRUE, NULL), ('Arroz', 'Chancay-Lambayeque', NULL, TRUE, NULL), ('Arroz', 'Jequetepeque', NULL, TRUE, NULL),
  ('Arroz', 'Jaen', NULL, TRUE, NULL), ('Arroz', 'Bagua - Utcubamba', NULL, TRUE, NULL), ('Arroz', 'Alto Mayo - Moyobamba', NULL, TRUE, NULL)
) AS v(cultivo, zona, ha, principal, fuente)
JOIN agro.cultivos c ON c.nombre = v.cultivo
JOIN agro.zonas z ON z.nombre = v.zona
ON CONFLICT (cultivo_id, zona_id, campania) DO UPDATE SET superficie_ha = EXCLUDED.superficie_ha, principal = EXCLUDED.principal, fuente = EXCLUDED.fuente;

-- 7. Superficie regional (DRAP Piura, campana 2025-2026) ---------------------
INSERT INTO agro.superficie_region (cultivo_id, region, campania, superficie_ha, fuente)
SELECT c.id, 'piura', '2025-2026', v.ha, 'DRAP Piura (Agropress, 01-09-2026)'
FROM (VALUES ('Arroz', 54424), ('Maiz amarillo duro', 25430), ('Maiz amilaceo', 12473), ('Trigo', 4769),
             ('Frijol caupi', 8658), ('Frijol grano seco', 6593), ('Arveja grano seco', 3859), ('Algodon Pima', 2091)) AS v(cultivo, ha)
JOIN agro.cultivos c ON c.nombre = v.cultivo
ON CONFLICT (cultivo_id, region, campania) DO UPDATE SET superficie_ha = EXCLUDED.superficie_ha;

-- 8. Acciones por fase (generales; las especificas por cultivo las agrega Alejandro) ----
INSERT INTO agro.acciones_etapa (cultivo_id, fase, descripcion, alerta_nasa, indicador) VALUES
 (NULL, 'S', 'Analisis de suelo, nivelacion y abonado de fondo; elegir variedad adaptada', 'Humedad del suelo (SMAP) y lluvia prevista (GPM IMERG)', 'humedad_suelo'),
 (NULL, 'C', 'Riego segun balance hidrico, fertilizacion nitrogenada y control de malezas', 'Anomalia de humedad del suelo; NDVI bajo = estres', 'ndvi'),
 (NULL, 'F', 'Evitar estres hidrico, monitorear plagas y polinizacion', 'Estres por calor (POWER T2M_MAX, ECOSTRESS)', 'calor'),
 (NULL, 'K', 'Planificar mano de obra, acopio y venta', 'Lluvia en los proximos dias (GPM IMERG)', 'lluvia'),
 (NULL, 'D', 'Sembrar cultivo de cobertura o leguminosa (rotacion) e incorporar materia organica', 'Meses de suelo desnudo (NDVI) y riesgo de erosion (SRTM + lluvia)', 'ndvi')
ON CONFLICT (cultivo_id, fase, descripcion) DO NOTHING;

INSERT INTO agro.acciones_etapa (cultivo_id, fase, descripcion, alerta_nasa, indicador)
SELECT c.id, v.fase, v.descripcion, v.alerta, v.indicador
FROM (VALUES
 ('Uva de mesa', 'D', 'Poda de produccion y aplicacion de cianamida para uniformizar la brotacion', 'Horas de calor (POWER T2M) para fechar la poda', 'calor'),
 ('Uva de mesa', 'K', 'Proteger racimos y adelantar cosecha si se anuncian lluvias', 'Lluvia anomala (GPM IMERG) y temperatura del mar (MUR SST)', 'lluvia'),
 ('Mango', 'F', 'Riego controlado (estres moderado) para inducir floracion; vigilar oidio y trips', 'Temperatura minima (POWER) y humedad', 'calor'),
 ('Mango', 'K', 'Planificar cosecha y acopio antes de las lluvias de verano', 'Lluvia anomala y senal de El Nino costero (MUR SST)', 'sst'),
 ('Limon', 'F', 'Riego y nutricion para asegurar floracion; vigilar plagas', 'Floracion baja si hay calor o sequia (POWER, SMAP)', 'humedad_suelo'),
 ('Limon', 'K', 'Drenaje de parcelas y control de hongos en anos con lluvia', 'El Nino costero: lluvia extrema (GPM IMERG)', 'lluvia'),
 ('Arroz', 'S', 'Sembrar solo con agua asegurada en el reservorio (Poechos / San Lorenzo)', 'Lluvia en la cuenca (GPM IMERG) y humedad del suelo (SMAP)', 'lluvia'),
 ('Banano organico', 'C', 'Vigilar marchitez por Fusarium; evaluar sandia u otra rotacion en focos', 'Exceso de humedad del suelo (SMAP)', 'humedad_suelo')
) AS v(cultivo, fase, descripcion, alerta, indicador)
JOIN agro.cultivos c ON c.nombre = v.cultivo
ON CONFLICT (cultivo_id, fase, descripcion) DO NOTHING;

-- 9. Rotaciones candidatas (solo cultivos anuales) -----------------------------
INSERT INTO agro.rotaciones (nombre, cultivo1_id, cultivo2_id, piso, beneficios, sacrificios)
SELECT v.nombre, c1.id, c2.id, v.piso, v.beneficios, v.sacrificios
FROM (VALUES
 ('Arroz - Maiz amarillo duro (practica comun)', 'Arroz', 'Maiz amarillo duro', 'costa', 'Referencia: secuencia mas comun en los valles', 'Alto consumo de agua; sin leguminosa que recupere el suelo'),
 ('Arroz - Frijol caupi',   'Arroz', 'Frijol caupi', 'costa', 'El caupi fija nitrogeno y usa poca agua', 'Menor ingreso que dos campanas de arroz'),
 ('Arroz - Zarandaja',      'Arroz', 'Zarandaja', 'costa', 'Leguminosa resistente a sequia; cubre el suelo', 'Mercado local mas pequeno'),
 ('Maiz amarillo duro - Frijol caupi', 'Maiz amarillo duro', 'Frijol caupi', 'costa', 'Menos agua que el arroz; aporta nitrogeno', 'Precio del maiz variable'),
 ('Algodon Pima - Frijol caupi', 'Algodon Pima', 'Frijol caupi', 'costa', 'Algodon de raiz profunda tolera sequia', 'Ciclo largo del algodon'),
 ('Sandia - Maiz amarillo duro', 'Sandia', 'Maiz amarillo duro', 'costa', 'Alternativa al banano con Fusarium; ciclo corto', 'Mercado sobre todo local'),
 ('Papa - Arveja grano seco', 'Papa', 'Arveja grano seco', 'sierra', 'La arveja fija nitrogeno tras la papa', 'Riesgo de heladas'),
 ('Maiz amilaceo - Trigo',  'Maiz amilaceo', 'Trigo', 'sierra', 'Rotacion tradicional de la sierra', 'Dependen de la lluvia')
) AS v(nombre, cul1, cul2, piso, beneficios, sacrificios)
JOIN agro.cultivos c1 ON c1.nombre = v.cul1
JOIN agro.cultivos c2 ON c2.nombre = v.cul2
ON CONFLICT (nombre) DO NOTHING;

-- 10. Datasets NASA ------------------------------------------------------------
INSERT INTO nasa.datasets (codigo, nombre, fuente, version, doi, proveedor, resolucion, requiere_login, uso) VALUES
 ('POWER',        'NASA POWER (AG community)',                'NASA POWER', NULL, NULL, 'LaRC', '0.5 grados (~55 km)', FALSE, 'Climatologia, temperatura, radiacion, humedad de raiz'),
 ('GPM_3IMERGM',  'GPM IMERG Final mensual',                  'GPM IMERG', '07', '10.5067/GPM/IMERG/3B-MONTH/07', 'GES DISC', '0.1 grados (~11 km)', TRUE, 'Lluvia por valle; maquina del tiempo 2017'),
 ('GPM_3IMERGDL', 'GPM IMERG Late diario',                    'GPM IMERG', '07', NULL, 'GES DISC', '0.1 grados', TRUE, 'Lluvia reciente'),
 ('SPL3SMP_E',    'SMAP L3 Enhanced 9 km',                    'SMAP', '006', NULL, 'NSIDC', '9 km', TRUE, 'Humedad del suelo'),
 ('MOD13Q1',      'MODIS Terra NDVI 16 dias',                 'MODIS NDVI', '061', '10.5067/MODIS/MOD13Q1.061', 'LP DAAC / ORNL', '250 m', FALSE, 'Vigor de cultivo'),
 ('MUR-JPL-L4-GLOB-v4.1', 'MUR SST',                          'MUR SST', '4.1', '10.5067/GHGMR-4FJ04', 'PO.DAAC / ERDDAP', '0.01 grados', FALSE, 'Senal de El Nino costero'),
 ('SRTMGL1',      'SRTM 1 arc-segundo',                       'SRTM', '003', '10.5067/MEaSUREs/SRTM/SRTMGL1.003', 'LP DAAC', '30 m', TRUE, 'Relieve y pendiente'),
 ('HLSL30',       'Harmonized Landsat Sentinel-2',            'HLS', '2.0', '10.5067/HLS/HLSL30.002', 'LP DAAC', '30 m', TRUE, 'NDVI de parcela'),
 ('ECO_L3T_JET',  'ECOSTRESS evapotranspiracion',             'ECOSTRESS', '003', NULL, 'LP DAAC', '70 m', TRUE, 'Demanda de agua (opcional)'),
 ('GLDAS_NOAH025_M', 'GLDAS Noah 0.25 mensual',               'GLDAS', '2.1', NULL, 'GES DISC', '0.25 grados', TRUE, 'Humedad del suelo historica')
ON CONFLICT (codigo) DO NOTHING;

-- 11. Eventos El Nino ----------------------------------------------------------
INSERT INTO nasa.eventos_enso (nombre, tipo, inicio, fin, intensidad, descripcion, fuente) VALUES
 ('El Nino 1997-1998', 'global',  '1997-05-01', '1998-06-30', 'extraordinario', 'Lluvias extremas en Piura (enero 1998: 16 mm/dia en POWER)', 'ENFEN / NOAA'),
 ('El Nino costero 2017', 'costero', '2017-01-01', '2017-04-30', 'fuerte', 'ONI neutral pero lluvia x5-x9 en valles de Piura (IMERG); invisible para indices globales', 'ENFEN; doc 24'),
 ('El Nino costero 2023', 'costero', '2023-03-01', '2023-12-31', 'moderado-fuerte', 'Calor y lluvias; afecto uva y mango', 'ENFEN'),
 ('El Nino 2026-2027', 'global',  '2026-05-01', NULL, 'en curso', 'ONI +2.46 en ASO 2026 (David); riesgo para limon, mango y arroz 2027', 'NOAA CPC; Agraria')
ON CONFLICT (nombre) DO NOTHING;
