@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "SCRIPT_START_HUMAN=%%t"
echo [deploy] Inicio: !SCRIPT_START_HUMAN!

REM ============================================================
REM AllpaShift - Despliegue Docker en el VPS
REM ============================================================
REM Flujo por servicio (modo directo, por defecto):
REM   1) build.bat compila (Java/Python/Vue)
REM   2) docker build local de la imagen
REM   3) docker save -> scp al VPS -> docker load
REM   4) docker compose up en el VPS (contexto Docker por SSH)
REM Si el contexto activo es local (desktop-linux/default) no hay transferencia.
REM Compose: deploy\vps\docker-compose.stack.yml (PostgreSQL)
REM          deploy\vps\docker-compose.app.yml   (aplicacion)
REM Configuracion: deploy\vps\.env  (copiar de .env.example)
REM Contexto: set-context.bat
REM ============================================================

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
set "JAVA_DIR=%REPO_ROOT%\02. backend\java"
set "PYTHON_DIR=%REPO_ROOT%\02. backend\python"
set "FRONTEND_DIR=%REPO_ROOT%\03. frontend"
set "VPS_DIR=%REPO_ROOT%\deploy\vps"
set "COMPOSE_APP=%VPS_DIR%\docker-compose.app.yml"
set "COMPOSE_STACK=%VPS_DIR%\docker-compose.stack.yml"
set "ENV_FILE=%VPS_DIR%\.env"
set "DEPLOY_LOG_DIR=%REPO_ROOT%\deploy-logs"
if not exist "!DEPLOY_LOG_DIR!" mkdir "!DEPLOY_LOG_DIR!"
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format ddMMyyyy-HHmmss"') do set "DEPLOY_LOG_TS=%%t"

set "JAVA_SERVICES=api-gateway agro-service"
set "PYTHON_SERVICES=climate-service"
set "BACKEND_SERVICES=%JAVA_SERVICES% %PYTHON_SERVICES%"
set "FRONTEND_SERVICE=frontend"
set "ALL_APP_SERVICES=%BACKEND_SERVICES% %FRONTEND_SERVICE%"

REM ---------- Valores por defecto (se sobreescriben con deploy\vps\.env) ----------
set "IMAGE_REGISTRY=allpashift"
set "IMAGE_TAG=latest"
set "DOCKER_PLATFORM=linux/amd64"
set "SSH_USER=root"
set "SSH_HOST="
set "PUBLIC_HTTP_PORT=80"
if exist "!ENV_FILE!" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("!ENV_FILE!") do (
        if /i "%%a"=="IMAGE_REGISTRY" set "IMAGE_REGISTRY=%%b"
        if /i "%%a"=="IMAGE_TAG" set "IMAGE_TAG=%%b"
        if /i "%%a"=="DOCKER_PLATFORM" set "DOCKER_PLATFORM=%%b"
        if /i "%%a"=="SSH_USER" set "SSH_USER=%%b"
        if /i "%%a"=="SSH_HOST" set "SSH_HOST=%%b"
        if /i "%%a"=="PUBLIC_HTTP_PORT" set "PUBLIC_HTTP_PORT=%%b"
        if /i "%%a"=="BUILD_MODE" set "BUILD_MODE=%%b"
    )
)

REM ---------- Contexto Docker activo (set-context.bat) ----------
set "ENTORNO_FILE=%REPO_ROOT%\deploy\entorno-activo.txt"
set "DOCKER_CTX=allpashift-vps"
if exist "!ENTORNO_FILE!" for /f "usebackq delims=" %%e in ("!ENTORNO_FILE!") do set "DOCKER_CTX=%%e"
set "DOCKER_CTX_BUILD=default"
docker context inspect desktop-linux >nul 2>&1 && set "DOCKER_CTX_BUILD=desktop-linux"
set "MODO_LOCAL=0"
if /i "!DOCKER_CTX!"=="!DOCKER_CTX_BUILD!" set "MODO_LOCAL=1"
if /i "!DOCKER_CTX!"=="default" set "MODO_LOCAL=1"
if /i "!DOCKER_CTX!"=="desktop-linux" set "MODO_LOCAL=1"
if /i "!BUILD_MODE!"=="auto" (
    set "BUILD_MODE=local"
    docker --context !DOCKER_CTX_BUILD! version --format "{{.Server.Version}}" >nul 2>&1 || set "BUILD_MODE=remote"
)
if "!MODO_LOCAL!"=="1" set "BUILD_MODE=local"
set "BUILD_CTX=!DOCKER_CTX_BUILD!"
if /i "!BUILD_MODE!"=="remote" set "BUILD_CTX=!DOCKER_CTX!"
set "PUBLIC_HOST=!SSH_HOST!"
if "!MODO_LOCAL!"=="1" set "PUBLIC_HOST=localhost"

for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "CYAN=%ESC%[96m"
set "RESET=%ESC%[0m"

set "FORCE=0"
set "NO_BUILD=0"
set "DOCKER_NO_CACHE=0"
set "SERVICIOS="
set "SERVICIOS_COUNT=0"
for %%a in (%*) do (
    set "ARG=%%a"
    if /i "%%a"=="--force" set "FORCE=1"
    if /i "%%a"=="--no-build" set "NO_BUILD=1"
    if /i "%%a"=="--no-cache" set "DOCKER_NO_CACHE=1"
    if not "!ARG:~0,2!"=="--" (
        set "SERVICIOS=!SERVICIOS! %%a"
        set /a SERVICIOS_COUNT+=1
    )
)
set "JAVA_COMPILADO=0"

if !SERVICIOS_COUNT! geq 2 goto :deployMultiple
if "%~1"=="" goto :showMenu
if /i "%~1"=="menu" goto :showMenu
if /i "%~1"=="backend" goto :deployBackend
if /i "%~1"=="frontend" goto :deployFrontend
if /i "%~1"=="all" goto :deployAll
if /i "%~1"=="stack" goto :deployStack
if /i "%~1"=="status" goto :remoteStatus
if /i "%~1"=="logs" goto :remoteLogs
if /i "%~1"=="context" goto :checkContext
if /i "%~1"=="list" goto :listServices
if /i "%~1"=="prune" goto :pruneRemote
if /i "%~1"=="help" goto :showHelp
set "SERVICIOS=%~1"
goto :deployMultiple

:showMenu
echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%  AllpaShift - Deploy [contexto: !DOCKER_CTX! ^| build: !DOCKER_CTX_BUILD!]%RESET%
echo %CYAN%  Imagenes: !IMAGE_REGISTRY!/^<servicio^>:!IMAGE_TAG! ^| plataforma !DOCKER_PLATFORM!%RESET%
if "!MODO_LOCAL!"=="1" (
    echo %CYAN%  Modo: LOCAL - sin transferencia%RESET%
) else (
    echo %CYAN%  Modo: VPS !SSH_USER!@!SSH_HOST! - build !BUILD_MODE!%RESET%
)
echo %CYAN%============================================================%RESET%
echo.
echo   1. Desplegar backend (%BACKEND_SERVICES%)
echo   2. Desplegar frontend
echo   3. Desplegar backend + frontend
echo   4. Desplegar un servicio
echo   5. Stack infra (PostgreSQL 17)
echo   6. Estado de contenedores
echo   7. Verificar contexto Docker
echo   8. Listar servicios
echo   P. Limpiar imagenes sin uso en el servidor
echo   0. Salir
echo.
set /p "OPTION=  Seleccione: "
if "%OPTION%"=="1" goto :deployBackend
if "%OPTION%"=="2" goto :deployFrontend
if "%OPTION%"=="3" goto :deployAll
if "%OPTION%"=="4" goto :selectService
if "%OPTION%"=="5" goto :deployStack
if "%OPTION%"=="6" goto :remoteStatus
if "%OPTION%"=="7" goto :checkContext
if "%OPTION%"=="8" goto :listServices
if /i "%OPTION%"=="P" goto :pruneRemote
if "%OPTION%"=="0" goto :endScript
goto :showMenu

:selectService
echo Servicios: %ALL_APP_SERVICES%
set /p "SERVICIOS=  Nombre: "
if "!SERVICIOS!"=="" goto :endScript
goto :deployMultiple

:listServices
echo.
echo %CYAN%Servicios desplegables:%RESET%
echo   %YELLOW%Java:%RESET%     %JAVA_SERVICES%
echo   %YELLOW%Python:%RESET%   %PYTHON_SERVICES%
echo   %YELLOW%Frontend:%RESET% %FRONTEND_SERVICE%
echo   %YELLOW%Infra:%RESET%    postgres ^(deploy.bat stack^)
echo.
echo   Ejemplos: deploy.bat all   ^|   deploy.bat agro-service frontend
goto :endScript

REM ============================================================
REM Verificaciones
REM ============================================================
:ensureEnv
if not exist "!ENV_FILE!" (
    echo %RED%[ERROR]%RESET% Falta deploy\vps\.env
    echo   Copie deploy\vps\.env.example a deploy\vps\.env y complete los valores.
    exit /b 1
)
exit /b 0

:ensureRemote
docker context inspect !DOCKER_CTX! >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% El contexto Docker '!DOCKER_CTX!' no existe.
    echo   docker context create allpashift-vps --docker "host=ssh://!SSH_USER!@ip-del-vps"
    echo   set-context.bat allpashift-vps
    exit /b 1
)
if "!MODO_LOCAL!"=="0" if "!SSH_HOST!"=="" (
    echo %RED%[ERROR]%RESET% SSH_HOST vacio en deploy\vps\.env
    exit /b 1
)
exit /b 0

:ensureNetwork
docker --context !DOCKER_CTX! network inspect allpashift_net >nul 2>&1
if errorlevel 1 (
    echo %CYAN%[NET]%RESET% Creando red allpashift_net...
    docker --context !DOCKER_CTX! network create allpashift_net >> "!DEPLOY_LOG!" 2>&1
    if errorlevel 1 exit /b 1
)
exit /b 0

:isKnownService
set "FOUND=0"
for %%s in (%ALL_APP_SERVICES%) do if /i "%%s"=="%~1" set "FOUND=1"
if "!FOUND!"=="0" exit /b 1
exit /b 0

REM ============================================================
REM Build de imagen (local)
REM ============================================================
:compileFor
set "SVC=%~1"
if "!NO_BUILD!"=="1" exit /b 0
for %%s in (%JAVA_SERVICES%) do if /i "%%s"=="!SVC!" (
    if "!JAVA_COMPILADO!"=="0" (
        echo %CYAN%[COMPILE]%RESET% Java - build.bat java
        call "%REPO_ROOT%\build.bat" java >nul
        if errorlevel 1 (
            echo %RED%[ERROR]%RESET% Fallo build.bat java. Revise build-logs\
            exit /b 1
        )
        set "JAVA_COMPILADO=1"
    )
)
exit /b 0

:serviceDir
set "SVC_DIR="
for %%s in (%JAVA_SERVICES%) do if /i "%%s"=="%~1" set "SVC_DIR=!JAVA_DIR!\%%s"
for %%s in (%PYTHON_SERVICES%) do if /i "%%s"=="%~1" set "SVC_DIR=!PYTHON_DIR!\%%s"
if /i "%~1"=="frontend" set "SVC_DIR=!FRONTEND_DIR!"
if not defined SVC_DIR exit /b 1
exit /b 0

:buildImage
set "SVC=%~1"
set "DEPLOY_LOG=!DEPLOY_LOG_DIR!\deploy-build-!SVC!-!DEPLOY_LOG_TS!.log"
set "IMAGE=!IMAGE_REGISTRY!/!SVC!:!IMAGE_TAG!"
call :compileFor "!SVC!" || exit /b 1
call :serviceDir "!SVC!" || exit /b 1
if not exist "!SVC_DIR!\Dockerfile" (
    echo %RED%[ERROR]%RESET% No existe Dockerfile en !SVC_DIR!
    exit /b 1
)
set "BUILD_NO_CACHE="
if "!DOCKER_NO_CACHE!"=="1" set "BUILD_NO_CACHE=--no-cache"
echo %CYAN%[BUILD]%RESET% !SVC! -^> !IMAGE! - !DOCKER_PLATFORM! - en !BUILD_CTX!
docker --context !BUILD_CTX! build !BUILD_NO_CACHE! --platform !DOCKER_PLATFORM! -t !IMAGE! "!SVC_DIR!" > "!DEPLOY_LOG!" 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% Build de imagen fallo. Ver: !DEPLOY_LOG!
    exit /b 1
)
echo %GREEN%[OK]%RESET% Imagen lista: !IMAGE!
exit /b 0

REM ============================================================
REM Transferencia al VPS: docker save -> scp -> docker load
REM ============================================================
:transferImage
set "SVC=%~1"
set "IMAGE=!IMAGE_REGISTRY!/!SVC!:!IMAGE_TAG!"
if "!MODO_LOCAL!"=="1" exit /b 0
if /i "!BUILD_MODE!"=="remote" exit /b 0
set "DEPLOY_LOG=!DEPLOY_LOG_DIR!\deploy-transfer-!SVC!-!DEPLOY_LOG_TS!.log"
set "TAR=%TEMP%\allpashift-!SVC!-!DEPLOY_LOG_TS!.tar"
set "REMOTE_TAR=/tmp/allpashift-!SVC!-!DEPLOY_LOG_TS!.tar"
echo %CYAN%[TRANSFER]%RESET% 1/3 docker save !IMAGE!...
docker --context !DOCKER_CTX_BUILD! save !IMAGE! -o "!TAR!" > "!DEPLOY_LOG!" 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% docker save fallo. Ver: !DEPLOY_LOG!
    exit /b 1
)
set "TAR_MB=?"
for /f "usebackq delims=" %%s in (`powershell -NoProfile -Command "[math]::Round((Get-Item -LiteralPath '!TAR!').Length/1MB,1)"`) do set "TAR_MB=%%s"
echo %CYAN%[TRANSFER]%RESET% 2/3 scp !TAR_MB! MB -^> !SSH_USER!@!SSH_HOST!...
scp -o ConnectTimeout=20 -o ServerAliveInterval=30 "!TAR!" "!SSH_USER!@!SSH_HOST!:!REMOTE_TAR!" >> "!DEPLOY_LOG!" 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% scp fallo. Ver: !DEPLOY_LOG!
    if exist "!TAR!" del /f /q "!TAR!" >nul 2>&1
    exit /b 1
)
echo %CYAN%[TRANSFER]%RESET% 3/3 docker load en el VPS...
ssh -o ConnectTimeout=20 !SSH_USER!@!SSH_HOST! "docker load -i !REMOTE_TAR! && rm -f !REMOTE_TAR!" >> "!DEPLOY_LOG!" 2>&1
set "LOAD_ERR=!errorlevel!"
if exist "!TAR!" del /f /q "!TAR!" >nul 2>&1
if !LOAD_ERR! neq 0 (
    echo %RED%[ERROR]%RESET% docker load fallo. Ver: !DEPLOY_LOG!
    exit /b 1
)
docker --context !DOCKER_CTX_BUILD! rmi -f !IMAGE! >> "!DEPLOY_LOG!" 2>&1
echo %GREEN%[OK]%RESET% Imagen en el VPS: !IMAGE!
exit /b 0

REM ============================================================
REM docker compose up en el servidor
REM ============================================================
:composeUp
set "COMPOSE_SVCS=%~1"
set "DEPLOY_LOG=!DEPLOY_LOG_DIR!\deploy-up-!DEPLOY_LOG_TS!.log"
call :ensureNetwork || exit /b 1
echo %CYAN%[UP]%RESET% !DOCKER_CTX!: !COMPOSE_SVCS!
docker --context !DOCKER_CTX! compose -f "!COMPOSE_APP!" --env-file "!ENV_FILE!" up -d --no-deps --pull never !COMPOSE_SVCS! >> "!DEPLOY_LOG!" 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% docker compose up fallo. Ver: !DEPLOY_LOG!
    powershell -NoProfile -Command "Get-Content -LiteralPath '!DEPLOY_LOG!' -Tail 6 -ErrorAction SilentlyContinue"
    exit /b 1
)
echo %GREEN%[OK]%RESET% Servicios activos: !COMPOSE_SVCS!
exit /b 0

:deployGroup
call :ensureEnv || goto :endScript
call :ensureRemote || goto :endScript
set "FALLO=0"
for %%s in (!GROUP!) do (
    if "!NO_BUILD!"=="0" (
        call :buildImage "%%s" || set "FALLO=1"
        if "!FALLO!"=="0" call :transferImage "%%s" || set "FALLO=1"
    )
)
if "!FALLO!"=="1" goto :endScript
call :composeUp "!GROUP!" || goto :endScript
call :printUrls
goto :endScript

:deployBackend
set "GROUP=%BACKEND_SERVICES%"
goto :deployGroup

:deployFrontend
set "GROUP=%FRONTEND_SERVICE%"
goto :deployGroup

:deployAll
set "GROUP=%ALL_APP_SERVICES%"
goto :deployGroup

:deployMultiple
set "GROUP="
for %%s in (!SERVICIOS!) do (
    call :isKnownService "%%s"
    if errorlevel 1 (
        echo %RED%[ERROR]%RESET% Servicio desconocido: %%s - ver deploy.bat list
    ) else (
        set "GROUP=!GROUP! %%s"
    )
)
if "!GROUP!"=="" goto :endScript
goto :deployGroup

:deployStack
call :ensureEnv || goto :endScript
call :ensureRemote || goto :endScript
set "DEPLOY_LOG=!DEPLOY_LOG_DIR!\deploy-stack-!DEPLOY_LOG_TS!.log"
echo %CYAN%[STACK]%RESET% PostgreSQL 17 en !DOCKER_CTX!...
call :ensureNetwork || goto :endScript
docker --context !DOCKER_CTX! compose -f "!COMPOSE_STACK!" --env-file "!ENV_FILE!" up -d > "!DEPLOY_LOG!" 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% Stack fallo. Ver: !DEPLOY_LOG!
    goto :endScript
)
echo %GREEN%[OK]%RESET% PostgreSQL activo ^(contenedor allpashift-postgres^).
echo   Siguiente paso: database-deploy.bat create
goto :endScript

:printUrls
echo.
echo   Web:         http://!PUBLIC_HOST!:!PUBLIC_HTTP_PORT!
echo   API Gateway: http://!PUBLIC_HOST!:!PUBLIC_HTTP_PORT!/api/agro/health
echo                http://!PUBLIC_HOST!:!PUBLIC_HTTP_PORT!/api/climate/health
exit /b 0

:remoteStatus
call :ensureRemote || goto :endScript
echo %CYAN%Contenedores en !DOCKER_CTX!:%RESET%
docker --context !DOCKER_CTX! ps --filter "name=allpashift" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
goto :endScript

:remoteLogs
call :ensureRemote || goto :endScript
if "%~2"=="" (
    echo Uso: deploy.bat logs ^<servicio^>
    goto :endScript
)
docker --context !DOCKER_CTX! logs allpashift-%~2 --tail 100
goto :endScript

:checkContext
echo Contextos Docker:
docker context ls
echo.
echo Contexto activo deploy: !DOCKER_CTX!  ^|  build local: !DOCKER_CTX_BUILD!
docker --context !DOCKER_CTX! info --format "Servidor: {{.Name}} - Docker {{.ServerVersion}}" 2>nul
goto :endScript

:pruneRemote
call :ensureRemote || goto :endScript
echo %CYAN%[PRUNE]%RESET% Eliminando imagenes sin uso en !DOCKER_CTX!...
docker --context !DOCKER_CTX! image prune -a -f
docker --context !DOCKER_CTX! builder prune -f
goto :endScript

:showHelp
echo.
echo %CYAN%Uso:%RESET% deploy.bat ^<comando^|servicio...^> [--no-build] [--no-cache] [--force]
echo.
echo   stack               PostgreSQL 17 ^(una vez; luego database-deploy.bat create^)
echo   backend             %BACKEND_SERVICES%
echo   frontend            %FRONTEND_SERVICE%
echo   all                 backend + frontend
echo   ^<servicio^> [...]    uno o varios: %ALL_APP_SERVICES%
echo   status              docker ps en el servidor
echo   logs ^<servicio^>     ultimas 100 lineas de log
echo   context             verificar contexto Docker
echo   list                listar servicios
echo   prune               limpiar imagenes sin uso en el servidor
echo   menu / help
echo.
echo   --no-build   solo docker compose up ^(imagen ya cargada en el servidor^)
echo   --no-cache   docker build sin cache
echo.
echo   Configuracion: deploy\vps\.env  ^|  Contexto: set-context.bat
goto :endScript

:endScript
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "SCRIPT_END_HUMAN=%%t"
echo [deploy] Fin: !SCRIPT_END_HUMAN!
endlocal
