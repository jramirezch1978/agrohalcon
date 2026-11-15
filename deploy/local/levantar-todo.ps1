# Levanta AllpaShift COMPLETO en tu PC, sin Docker:
#   PostgreSQL embebido -> calculos (:8001) y climate-service (:8000) -> agro-service Java (:8081) -> api-gateway (:8080) -> frontend (:5173)
#
#   .\deploy\local\levantar-todo.ps1                      # usa JAVA_HOME (Java 17+) y el venv de climate-service
#   .\deploy\local\levantar-todo.ps1 -JavaHome "D:\herramientas\jdk-17"
#   .\deploy\local\levantar-todo.ps1 -Recrear             # borra y vuelve a cargar la base de datos
#   .\deploy\local\levantar-todo.ps1 -Recompilar          # recompila la API Java (después de cambiar código Java)
#   .\deploy\local\detener-todo.ps1                       # lo apaga todo
#
# Requisitos (una sola vez): Java 17+, Node 20+, Python 3.11 con el venv de climate-service (ver deploy/local/README.md).
# La clave de Groq es opcional:  $env:GROQ_API_KEY = "..."  antes de correr el script (sin ella el asistente responde en modo respaldo).
param(
    [string]$JavaHome = $env:JAVA_HOME,
    [switch]$Recrear,
    [switch]$Recompilar,   # vuelve a compilar la API Java aunque ya haya jars (úsalo después de cambiar código Java)
    [switch]$SinFrontend
)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$local = $PSScriptRoot
$logs = Join-Path $local ".logs"
New-Item -ItemType Directory -Force $logs | Out-Null
$py = Join-Path $repo "02. backend\python\climate-service\.venv\Scripts\python.exe"

function Fallo($m) { Write-Host "✗ $m" -ForegroundColor Red; exit 1 }
function Ok($m) { Write-Host "✓ $m" -ForegroundColor Green }

# ---- 1) requisitos
if (-not (Test-Path $py)) { Fallo "Falta el venv de Python: crea 02. backend\python\climate-service\.venv (py -3.11 -m venv .venv; .\.venv\Scripts\pip install -r requirements-dev.txt pandas pyyaml tzdata pgserver 'psycopg[binary]')" }
if (-not $JavaHome -or -not (Test-Path (Join-Path $JavaHome "bin\java.exe"))) { Fallo "Falta Java 17+: pasa -JavaHome <carpeta del JDK> o define JAVA_HOME" }
$env:JAVA_HOME = $JavaHome
$env:Path = "$JavaHome\bin;$env:Path"
$version = (cmd /c "java -version 2>&1" | Select-Object -First 1)
if ($version -notmatch '"(1[7-9]|[2-9]\d)\.') { Fallo "Se necesita Java 17 o mayor y encontré: $version" }
Ok "Java: $version"

# ---- 2) PostgreSQL embebido con el esquema y los seeds del equipo
$salida = & $py -X utf8 (Join-Path $local "pg_local.py") $(if ($Recrear) { "--recrear" }) 2>&1
$salida | ForEach-Object { Write-Host "  $_" }
$puerto = ($salida | Where-Object { $_ -match '^PUERTO=(\d+)$' } | ForEach-Object { $Matches[1] } | Select-Object -Last 1)
if (-not $puerto) { Fallo "No pude arrancar PostgreSQL embebido (mira la salida de arriba)" }
Ok "PostgreSQL embebido en el puerto $puerto"

# ---- 3) compilar los jars si faltan
foreach ($m in "agro-service", "api-gateway") {
    $dir = Join-Path $repo "02. backend\java\$m"
    if ($Recompilar -or -not (Get-ChildItem (Join-Path $dir "target") -Filter "$m-*.jar" -ErrorAction SilentlyContinue)) {
        Write-Host "  compilando $m (la primera vez baja dependencias de Maven)…"
        Push-Location $dir; & .\mvnw.cmd -B -ntp -q -DskipTests package; $rc = $LASTEXITCODE; Pop-Location
        if ($rc -ne 0) { Fallo "Falló la compilación de $m" }
    }
}
Ok "API Java compilada"

# ---- 4) procesos (cada uno con su registro en deploy\local\.logs y su PID en .pids)
$pids = @()
function Arrancar($nombre, $exe, $argumentos, $carpeta, $entorno = @{}) {
    $viejo = @{}
    foreach ($k in $entorno.Keys) { $viejo[$k] = [Environment]::GetEnvironmentVariable($k); [Environment]::SetEnvironmentVariable($k, $entorno[$k]) }
    $p = Start-Process -FilePath $exe -ArgumentList $argumentos -WorkingDirectory $carpeta -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logs "$nombre.log") -RedirectStandardError (Join-Path $logs "$nombre.err.log")
    foreach ($k in $entorno.Keys) { [Environment]::SetEnvironmentVariable($k, $viejo[$k]) }
    $script:pids += "$nombre=$($p.Id)"
    Ok "$nombre (pid $($p.Id))"
}
function Esperar($url, $segundos = 120) {
    $fin = (Get-Date).AddSeconds($segundos)
    while ((Get-Date) -lt $fin) { try { Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 3 | Out-Null; return $true } catch { Start-Sleep -Seconds 2 } }
    return $false
}

Arrancar "calculos" $py "-W ignore -m uvicorn app.main:app --port 8001" (Join-Path $repo "02. backend\python\calculos")
Arrancar "climate-service" $py "-m uvicorn app.main:app --port 8000" (Join-Path $repo "02. backend\python\climate-service")
$jarAgro = (Get-ChildItem (Join-Path $repo "02. backend\java\agro-service\target") -Filter "agro-service-*.jar" | Where-Object { $_.Name -notmatch "original" } | Select-Object -First 1).FullName
$jarGw = (Get-ChildItem (Join-Path $repo "02. backend\java\api-gateway\target") -Filter "api-gateway-*.jar" | Where-Object { $_.Name -notmatch "original" } | Select-Object -First 1).FullName
Arrancar "agro-service" (Join-Path $JavaHome "bin\java.exe") "-jar `"$jarAgro`"" (Join-Path $repo "02. backend\java\agro-service") @{
    SPRING_DATASOURCE_URL = "jdbc:postgresql://127.0.0.1:$puerto/postgres"; SPRING_DATASOURCE_USERNAME = "postgres"; SPRING_DATASOURCE_PASSWORD = "local"
    CALCULOS_URL = "http://localhost:8001"; GROQ_API_KEY = $env:GROQ_API_KEY }
Arrancar "api-gateway" (Join-Path $JavaHome "bin\java.exe") "-jar `"$jarGw`"" (Join-Path $repo "02. backend\java\api-gateway") @{
    AGRO_SERVICE_URL = "http://localhost:8081"; CLIMATE_SERVICE_URL = "http://localhost:8000" }
if (-not $SinFrontend) {
    $front = Join-Path $repo "03. frontend"
    if (-not (Test-Path (Join-Path $front "node_modules"))) { Write-Host "  npm ci (la primera vez)…"; Push-Location $front; npm ci --no-audit --no-fund | Out-Null; Pop-Location }
    if (-not (Test-Path (Join-Path $front ".env"))) { "VITE_CALCULOS_URL=`nVITE_USE_MOCK=false`nVITE_API_URL=http://localhost:8080`n" | Set-Content (Join-Path $front ".env") -Encoding ascii }
    Arrancar "frontend" "cmd.exe" "/c npm run dev" $front
}
$pids | Set-Content (Join-Path $local ".pids")

# ---- 5) esperar y avisar
Write-Host "Esperando a que responda todo (la API Java tarda ~20 s)…"
$estado = [ordered]@{ "calculos :8001" = "http://localhost:8001/salud"; "climate-service :8000" = "http://localhost:8000/salud"; "API (gateway :8080 → agro-service → calculos)" = "http://localhost:8080/api/salud" }
if (-not $SinFrontend) { $estado["frontend :5173"] = "http://localhost:5173/" }
foreach ($e in $estado.GetEnumerator()) { if (Esperar $e.Value) { Ok $e.Key } else { Write-Host "✗ $($e.Key) no respondió: mira deploy\local\.logs" -ForegroundColor Yellow } }
Write-Host "`nListo:  http://localhost:5173   (app)   ·   http://localhost:8000/panel/   (panel técnico de David)" -ForegroundColor Cyan
Write-Host "Asistente de IA: $(if ($env:GROQ_API_KEY) { 'con Groq' } else { 'modo respaldo (sin GROQ_API_KEY)' })"
