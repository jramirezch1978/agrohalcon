# DDL — modelo relacional de AllpaShift (PostgreSQL 17)

| Archivo | Contenido |
|---|---|
| `00-schema.sql` | Esquemas `agro`, `nasa` y `ref`: 20 tablas y 2 vistas con la forma del contrato |
| `seed/01-catalogo-norte.sql` | 7 regiones, 18 valles, 37 cultivos, calendario, superficies DRAP, acciones, rotaciones, datasets NASA y eventos El Niño. Se puede ejecutar varias veces sin duplicar |
| `99-resumen.sql` | Conteo de filas por tabla |

Documentación del modelo (diagrama entidad-relación y descripción de cada tabla): [26_modelo_base_de_datos](../../01.%20documentacion/26_modelo_base_de_datos.md).

Para cargarlo en el VPS: `database-deploy.bat create --force` (borra y recrea los esquemas) o `database-deploy.bat seed` (solo los datos).

⚠️ Los calendarios y los Kc son **preliminares**. Alejandro los valida en `feature/catalogo-cultivos`.
