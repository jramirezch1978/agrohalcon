@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM AllpaShift - Selector de contexto Docker para deploy.bat / database-deploy.bat
REM ============================================================
REM Sin argumentos -> menu con los contextos Docker existentes (docker context ls).
REM Con argumento   -> set-context.bat <contexto>
REM   Solo acepta contextos que YA existen; no crea contextos.
REM La eleccion se guarda en deploy\entorno-activo.txt
REM
REM Crear el contexto del VPS (una sola vez):
REM   docker context create allpashift-vps --docker "host=ssh://usuario@ip-del-vps"
REM Contexto local (pruebas): desktop-linux / default
REM ============================================================

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
set "ENTORNO_FILE=%REPO_ROOT%\deploy\entorno-activo.txt"

set "ENTORNO_ACTUAL="
if exist "!ENTORNO_FILE!" set /p ENTORNO_ACTUAL=<"!ENTORNO_FILE!"

call :listarContextos
if "!CTX_COUNT!"=="0" (
    echo [ERROR] No se encontraron contextos Docker configurados.
    echo   Verifique con: docker context ls
    endlocal
    exit /b 1
)

if not "%~1"=="" goto :seleccionDirecta

set "REINTENTOS=0"
:menu
echo.
echo ============================================================
echo   AllpaShift - Seleccionar contexto activo
echo ============================================================
if defined ENTORNO_ACTUAL (
    echo   Contexto activo actual: !ENTORNO_ACTUAL!
) else (
    echo   Contexto activo actual: no configurado
)
echo.
echo   Contextos Docker disponibles:
for /l %%i in (1,1,!CTX_COUNT!) do (
    set "MARCA= "
    if /i "!CTX_%%i!"=="!ENTORNO_ACTUAL!" set "MARCA=*"
    echo     %%i. !CTX_%%i! !MARCA!
)
echo     0. Cancelar
echo.
set "OPCION="
set /p "OPCION=  Seleccione el numero de contexto: "
if "!OPCION!"=="0" goto :cancelado
set "ENTORNO="
for /l %%i in (1,1,!CTX_COUNT!) do if "!OPCION!"=="%%i" set "ENTORNO=!CTX_%%i!"
if not defined ENTORNO (
    echo   [ERROR] Opcion invalida: '!OPCION!'
    set /a REINTENTOS+=1
    if !REINTENTOS! geq 5 goto :cancelado
    goto :menu
)
goto :guardar

:seleccionDirecta
set "ENTORNO=%~1"
set "ENCONTRADO=0"
for /l %%i in (1,1,!CTX_COUNT!) do if /i "!CTX_%%i!"=="!ENTORNO!" set "ENCONTRADO=1"
if "!ENCONTRADO!"=="0" (
    echo [ERROR] El contexto Docker '!ENTORNO!' no existe todavia.
    echo.
    echo   Contextos disponibles:
    for /l %%i in (1,1,!CTX_COUNT!) do echo     - !CTX_%%i!
    echo.
    echo   Para crearlo:
    echo     docker context create !ENTORNO! --docker "host=ssh://usuario@ip-del-vps"
    endlocal
    exit /b 1
)

:guardar
if not exist "%REPO_ROOT%\deploy" mkdir "%REPO_ROOT%\deploy"
> "!ENTORNO_FILE!" echo !ENTORNO!
echo.
echo [OK] Contexto activo: !ENTORNO!
echo   Compose: deploy\vps\docker-compose.stack.yml + docker-compose.app.yml
echo   Ya puede usar: deploy.bat  /  database-deploy.bat
endlocal
exit /b 0

:cancelado
echo Operacion cancelada. Contexto sin cambios.
endlocal
exit /b 1

:listarContextos
set "CTX_COUNT=0"
for /f "usebackq delims=" %%c in (`docker context ls --format "{{.Name}}" 2^>nul`) do (
    set /a CTX_COUNT+=1
    set "CTX_!CTX_COUNT!=%%c"
)
exit /b 0
