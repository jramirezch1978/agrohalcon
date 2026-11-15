@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "SCRIPT_START_HUMAN=%%t"
echo [database-deploy] Inicio: !SCRIPT_START_HUMAN!

REM ============================================================
REM AllpaShift - database-deploy.bat (DDL y seed de PostgreSQL)
REM ============================================================
REM Ejecuta los scripts de "04. base de datos\ddl" con psql DENTRO del
REM contenedor allpashift-postgres (docker exec), usando el contexto
REM Docker activo (set-context.bat). No necesita abrir el puerto 5432.
REM
REM   database-deploy.bat create [--force]   esquema + seed
REM   database-deploy.bat schema             solo DDL (00-schema.sql)
REM   database-deploy.bat seed               solo seed
REM   database-deploy.bat resumen            conteo de filas por tabla
REM   database-deploy.bat backup             pg_dump a deploy-logs\backups
REM   database-deploy.bat psql               consola psql interactiva
REM Credenciales: deploy\vps\.env (POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB)
REM ============================================================

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
set "ENV_FILE=%REPO_ROOT%\deploy\vps\.env"
set "DDL_DIR=%REPO_ROOT%\04. base de datos\ddl"
set "DEPLOY_LOG_DIR=%REPO_ROOT%\deploy-logs"
if not exist "!DEPLOY_LOG_DIR!" mkdir "!DEPLOY_LOG_DIR!"
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format ddMMyyyy-HHmmss"') do set "DBDEPLOY_TS=%%t"

set "PG_CONTAINER=allpashift-postgres"
set "PGUSER="
set "PGDATABASE="
if exist "!ENV_FILE!" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("!ENV_FILE!") do (
        if /i "%%a"=="POSTGRES_USER" set "PGUSER=%%b"
        if /i "%%a"=="POSTGRES_DB" set "PGDATABASE=%%b"
    )
) else (
    echo ERROR: Falta deploy\vps\.env ^(copie .env.example^)
    goto :fail
)
if not defined PGUSER (
    echo ERROR: POSTGRES_USER no definido en deploy\vps\.env
    goto :fail
)
if not defined PGDATABASE set "PGDATABASE=allpashift"

set "ENTORNO_FILE=%REPO_ROOT%\deploy\entorno-activo.txt"
set "DOCKER_CTX=allpashift-vps"
if exist "!ENTORNO_FILE!" for /f "usebackq delims=" %%e in ("!ENTORNO_FILE!") do set "DOCKER_CTX=%%e"

set "FORCE=0"
set "MODE="
for %%a in (%*) do (
    if /i "%%a"=="--force" (set "FORCE=1") else if not defined MODE set "MODE=%%a"
)
set "DBDEPLOY_LOG=!DEPLOY_LOG_DIR!\database-deploy-!MODE!-!DBDEPLOY_TS!.log"
(
echo ============================================================
echo DATABASE DEPLOY AllpaShift - !PGUSER!@!PG_CONTAINER!/!PGDATABASE! [contexto !DOCKER_CTX!]
echo Inicio: !SCRIPT_START_HUMAN!   Modo: !MODE!   Force: !FORCE!
echo ============================================================
) > "!DBDEPLOY_LOG!"

if "!MODE!"=="" goto :help
if /I "!MODE!"=="create" goto :route_create
if /I "!MODE!"=="schema" goto :route_schema
if /I "!MODE!"=="seed" goto :route_seed
if /I "!MODE!"=="resumen" goto :route_resumen
if /I "!MODE!"=="backup" goto :route_backup
if /I "!MODE!"=="psql" goto :route_psql
echo ERROR: Comando desconocido: !MODE!
goto :help

:route_create
call :check_container || goto :fail
echo.
echo ^>^> Modo: create  [esquema + seed]  Force: !FORCE!
if "!FORCE!"=="1" (
    echo ^>^> --force: eliminando esquemas agro, nasa y ref...
    call :psql_cmd "DROP SCHEMA IF EXISTS agro CASCADE; DROP SCHEMA IF EXISTS nasa CASCADE; DROP SCHEMA IF EXISTS ref CASCADE;" || goto :fail
)
echo.
echo ========== PASO 1/2: ESQUEMA ==========
call :run_sql "00-schema.sql" || goto :fail
echo.
echo ========== PASO 2/2: SEED ==========
call :run_sql "seed\01-catalogo-norte.sql" || goto :fail
call :run_sql "seed\03-salud-suelo.sql" || goto :fail
call :run_sql "99-resumen.sql" || goto :fail
goto :done

:route_schema
call :check_container || goto :fail
call :run_sql "00-schema.sql" || goto :fail
goto :done

:route_seed
call :check_container || goto :fail
call :run_sql "seed\01-catalogo-norte.sql" || goto :fail
call :run_sql "seed\03-salud-suelo.sql" || goto :fail
call :run_sql "99-resumen.sql" || goto :fail
goto :done

:route_resumen
call :check_container || goto :fail
call :run_sql "99-resumen.sql" || goto :fail
goto :done

:route_backup
call :check_container || goto :fail
if not exist "!DEPLOY_LOG_DIR!\backups" mkdir "!DEPLOY_LOG_DIR!\backups"
set "BACKUP_FILE=!DEPLOY_LOG_DIR!\backups\allpashift-!DBDEPLOY_TS!.sql"
echo ^>^> pg_dump -^> !BACKUP_FILE!
docker --context !DOCKER_CTX! exec !PG_CONTAINER! pg_dump -U !PGUSER! -d !PGDATABASE! --no-owner > "!BACKUP_FILE!" 2>> "!DBDEPLOY_LOG!"
if errorlevel 1 goto :fail
goto :done

:route_psql
call :check_container || goto :fail
docker --context !DOCKER_CTX! exec -it !PG_CONTAINER! psql -U !PGUSER! -d !PGDATABASE!
goto :done

REM ------------------------------------------------------------
:check_container
where docker >nul 2>&1 || (
    echo ERROR: Docker no esta en el PATH
    exit /b 1
)
docker --context !DOCKER_CTX! inspect -f "{{.State.Running}}" !PG_CONTAINER! 2>nul | findstr /i "true" >nul
if errorlevel 1 (
    echo ERROR: El contenedor !PG_CONTAINER! no esta corriendo en el contexto !DOCKER_CTX!.
    echo   Levantelo con: deploy.bat stack
    exit /b 1
)
exit /b 0

:psql_cmd
docker --context !DOCKER_CTX! exec -i !PG_CONTAINER! psql -U !PGUSER! -d !PGDATABASE! -v ON_ERROR_STOP=1 -c "%~1" >> "!DBDEPLOY_LOG!" 2>&1
exit /b %ERRORLEVEL%

:run_sql
set "REL=%~1"
if not exist "!DDL_DIR!\!REL!" (
    echo ERROR: No existe !DDL_DIR!\!REL!
    exit /b 1
)
echo ^>^> --- !REL! ---
(echo ^>^> --- !REL! ---)>> "!DBDEPLOY_LOG!"
set "RUNSQL_OUT=%TEMP%\allpashift_db_!RANDOM!_!RANDOM!.log"
docker --context !DOCKER_CTX! exec -i !PG_CONTAINER! psql -U !PGUSER! -d !PGDATABASE! -v ON_ERROR_STOP=1 < "!DDL_DIR!\!REL!" > "!RUNSQL_OUT!" 2>&1
set "RUNSQL_RC=!ERRORLEVEL!"
if exist "!RUNSQL_OUT!" (
    type "!RUNSQL_OUT!"
    type "!RUNSQL_OUT!" >> "!DBDEPLOY_LOG!"
    del "!RUNSQL_OUT!" >nul 2>&1
)
if !RUNSQL_RC! geq 1 exit /b 1
echo    OK
exit /b 0

:done
echo.
echo ^>^> Proceso completado exitosamente.
echo [database-deploy] Log: !DBDEPLOY_LOG!
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do echo [database-deploy] Fin: %%t
exit /b 0

:fail
echo.
echo ERROR: Fallo. Revise mensajes arriba y el log.
if defined DBDEPLOY_LOG echo [database-deploy] Log: !DBDEPLOY_LOG!
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do echo [database-deploy] Fin: %%t
exit /b 1

:help
echo.
echo Uso:
echo   %~nx0 create [--force]   esquema + seed ^(--force borra y recrea los esquemas agro, nasa y ref^)
echo   %~nx0 schema             solo DDL ^(00-schema.sql^)
echo   %~nx0 seed               solo seed del catalogo del norte
echo   %~nx0 resumen            conteo de filas por tabla
echo   %~nx0 backup             pg_dump a deploy-logs\backups
echo   %~nx0 psql               consola psql interactiva
echo.
echo Contenedor: !PG_CONTAINER! ^(contexto Docker: !DOCKER_CTX!^)
echo Scripts:    04. base de datos\ddl
echo Credenciales: deploy\vps\.env
exit /b 1
