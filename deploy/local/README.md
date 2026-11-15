# AllpaShift completo en tu PC (sin Docker)

Sirve para ver y probar **todo junto** como lo hace el VPS: app Vue → api-gateway → agro-service (Java) → PostgreSQL ← calculos (Python) → NASA.
No reemplaza al `deploy/vps/` (Docker); es para desarrollar y para verificar una rama antes del Pull Request.

```powershell
.\deploy\local\levantar-todo.ps1 -JavaHome "D:\herramientas\jdk-17"   # o define JAVA_HOME
# app: http://localhost:5173 · panel técnico: http://localhost:8000/panel/
.\deploy\local\detener-todo.ps1
```

| Pieza | Puerto | De dónde sale |
|---|---|---|
| app (Vite) | 5173 | `03. frontend` |
| api-gateway | 8080 | `02. backend/java/api-gateway` (jar compilado con `mvnw`) |
| agro-service | 8081 | `02. backend/java/agro-service` (lee y graba PostgreSQL, llama a calculos y a Groq) |
| calculos | 8001 | `02. backend/python/calculos` (descarga NASA y calcula) |
| climate-service | 8000 | `02. backend/python/climate-service` (panel técnico; Java ya no lo llama) |
| PostgreSQL | puerto libre (lo imprime el script) | `pgserver` embebido; carga `04. base de datos/ddl/00-schema.sql`, `seed/01-catalogo-norte.sql` y `seed/02-datos-nasa.sql` |

## Requisitos (una sola vez)
- **Java 17 o mayor.** Sin instalar nada: el zip de *Eclipse Temurin 17 JDK* (https://adoptium.net) descomprimido en una carpeta y `-JavaHome` apuntando a ella.
- **Node 20+** (`npm ci` lo corre el script la primera vez) y **Python 3.11** con el venv de `climate-service`:
  `py -3.11 -m venv .venv` y `.\.venv\Scripts\pip install -r requirements-dev.txt pandas pyyaml tzdata pgserver "psycopg[binary]"` (dentro de `02. backend/python/climate-service`).
- Opcional: `$env:GROQ_API_KEY = "..."` antes de correr el script para que el asistente use Groq (`openai/gpt-oss-20b`). Sin clave responde en **modo respaldo** (el `queHacer` calculado).

## Cosas que conviene saber
- Los registros de cada servicio quedan en `deploy/local/.logs/`; la base de datos en `deploy/local/.pgdata/` (ambos fuera de git). `-Recrear` borra y recarga la base.
- Java guarda cada resultado en `agro.consultas` y lo reutiliza **3 horas**: si cambias los cálculos y no ves el cambio, ejecuta `-Recrear` (o vacía esa tabla).
- El PostgreSQL de `pgserver` para Windows no trae zonas horarias; `pg_local.py` las copia desde el paquete `tzdata`. Sin ese paso la API falla con `invalid value for parameter "TimeZone"`.
- Es PostgreSQL 16, el VPS usa 17: el esquema corre igual (verificado), pero no es idéntico.
