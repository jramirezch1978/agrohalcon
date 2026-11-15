# Apaga lo que levantó levantar-todo.ps1 (procesos de .pids, sus hijos y el PostgreSQL embebido).
$local = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $local "..\..")).Path
$archivo = Join-Path $local ".pids"
if (Test-Path $archivo) {
    foreach ($linea in Get-Content $archivo) {
        $nombre, $id = $linea -split "="
        # taskkill /T también cierra los procesos hijos (uvicorn, npm → node…)
        taskkill /PID $id /T /F 2>&1 | Out-Null
        Write-Host "detenido $nombre (pid $id)"
    }
    Remove-Item $archivo
} else { Write-Host "no hay .pids: nada que detener" }
$py = Join-Path $repo "02. backend\python\climate-service\.venv\Scripts\python.exe"
if (Test-Path $py) { & $py -X utf8 (Join-Path $local "pg_local.py") --parar 2>&1 | Out-Null; Write-Host "PostgreSQL embebido detenido" }
