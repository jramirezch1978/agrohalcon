-- Semilla de la tabla zonas (AgroShift). Coordenadas aproximadas: validar con el catálogo.
INSERT INTO zonas (id, nombre, lat, lon, region) VALUES
  (1, 'Bajo Piura', -5.35, -80.7, 'piura'),
  (2, 'Valle del Chira', -4.9, -80.85, 'piura'),
  (3, 'Medio Piura - Castilla', -5.2, -80.62, 'piura'),
  (4, 'San Lorenzo - Tambogrande', -4.93, -80.34, 'piura'),
  (5, 'Alto Piura - Chulucanas', -5.1, -80.16, 'piura'),
  (6, 'Sechura - Bernal / Vice', -5.45, -80.8, 'piura'),
  (7, 'Sierra - Huancabamba', -5.24, -79.45, 'piura'),
  (8, 'Valle de Tumbes', -3.57, -80.45, 'tumbes'),
  (9, 'Chancay-Lambayeque', -6.7, -79.9, 'lambayeque'),
  (10, 'Olmos', -5.99, -79.74, 'lambayeque'),
  (11, 'Jequetepeque', -7.2, -79.45, 'la_libertad'),
  (12, 'Chavimochic - Virú', -8.41, -78.75, 'la_libertad'),
  (13, 'Jaén', -5.71, -78.81, 'cajamarca'),
  (14, 'Valle de Cajamarca', -7.16, -78.5, 'cajamarca'),
  (15, 'Bagua - Utcubamba', -5.64, -78.53, 'amazonas'),
  (16, 'Alto Mayo - Moyobamba', -6.03, -76.97, 'san_martin')
ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre, lat = EXCLUDED.lat, lon = EXCLUDED.lon, region = EXCLUDED.region;
