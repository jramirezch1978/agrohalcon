# Reconstruye todo con lo último que haya en la caché de descargas y vuelve a comprobarlo.
#   .\actualizar.ps1                 # base + PostgreSQL + panel + pruebas
#   .\actualizar.ps1 -Descargar      # además vuelve a bajar POWER, Niño, MUR y SRTM (usa el token de .env)
#   .\actualizar.ps1 -Catalogo ..\..\..\data\crops\cultivos.json   # con el catálogo REAL de Alejandro
param(
    [switch]$Descargar,
    [string]$Catalogo = ""
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = ".\.venv\Scripts\python.exe"

if ($Descargar) {
    & $py -X utf8 -m etl.jobs power nino mur srtm
}
if ($Catalogo) { & $py -X utf8 -W ignore -m db.build --catalogo $Catalogo } else { & $py -X utf8 -W ignore -m db.build }
& $py -X utf8 -W ignore -m db.export_postgres
& $py -X utf8 -W ignore -m db.export_allpashift   # seed para el esquema de Jhonny (04. base de datos/ddl/seed/02-datos-nasa.sql)
& $py -X utf8 -W ignore -m db.export_panel
& $py -X utf8 -m pytest -q
Write-Host "`nListo. Servicio y panel:  .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000   ->  http://localhost:8000/panel/"
