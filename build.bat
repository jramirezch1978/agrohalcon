@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "SCRIPT_START_HUMAN=%%t"
echo [build] Inicio: !SCRIPT_START_HUMAN!

REM ============================================================
REM AllpaShift - Build local (Windows)
REM   01. documentacion\           documentacion del proyecto
REM   02. backend\java\            microservicios Java 17 + Spring Boot (Maven multi-modulo)
REM                                  api-gateway (8080), agro-service (8081)
REM   02. backend\python\          microservicios Python + FastAPI (una carpeta por servicio)
REM                                  climate-service (8000), calculos (8001)
REM   03. frontend\                Vue 3 + Vite
REM   04. base de datos\           scripts y modelo de datos
REM   05. mobile\                  Capacitor 6 -> release\android (APK) y release\ios
REM Este script solo compila. Publicar es deploy.bat, aparte.
REM ============================================================

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
set "JAVA_DIR=%REPO_ROOT%\02. backend\java"
set "PYTHON_DIR=%REPO_ROOT%\02. backend\python"
set "FRONTEND_DIR=%REPO_ROOT%\03. frontend"
set "MOBILE_DIR=%REPO_ROOT%\05. mobile"
set "RELEASE_ANDROID=%MOBILE_DIR%\release\android"
set "RELEASE_IOS=%MOBILE_DIR%\release\ios"
set "JAVA_VERSION=17"
set "BUILD_LOG_DIR=%REPO_ROOT%\build-logs"
if not exist "!BUILD_LOG_DIR!" mkdir "!BUILD_LOG_DIR!"
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format ddMMyyyy-HHmmss"') do set "BUILD_LOG_TS=%%t"

for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "CYAN=%ESC%[96m"
set "RESET=%ESC%[0m"

set "BUILD_FAILED=0"
set "MOBILE_TARGET="
if "%~1"=="" goto :buildAll
if /i "%~1"=="all" goto :buildAll
if /i "%~1"=="backend" goto :cmdBackend
if /i "%~1"=="java" goto :cmdJava
if /i "%~1"=="python" goto :cmdPython
if /i "%~1"=="frontend" goto :cmdFrontend
if /i "%~1"=="mobile" goto :cmdMobile
if /i "%~1"=="compile" goto :compileAll
if /i "%~1"=="clean" goto :cleanAll
if /i "%~1"=="test" goto :testAll
if /i "%~1"=="menu" goto :showMenu
if /i "%~1"=="help" goto :showHelp
echo %RED%[ERROR]%RESET% Comando desconocido: %~1
goto :showHelp

:showMenu
echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%  AllpaShift - Build local (Windows)%RESET%
echo %CYAN%  Backend Java: Java %JAVA_VERSION% ^| Maven ^| Spring Boot ^| API Gateway%RESET%
echo %CYAN%  Backend Python: FastAPI%RESET%
echo %CYAN%  Frontend: Vue 3 ^| Vite ^| Node 20+%RESET%
echo %CYAN%  Mobile: Capacitor 6 ^| APK Android ^| iOS (compila en Mac)%RESET%
echo %CYAN%============================================================%RESET%
echo.
echo   1. Compilar TODO (backend + frontend)
echo   2. Compilar backend (Java + Python)
echo   3. Compilar frontend (Vue)
echo   4. Compilar mobile APK Android (por defecto)
echo   5. Compilar mobile AAB Android (Play Store)
echo   6. Generar mobile iOS (proyecto Xcode)
echo   7. Compilacion rapida de validacion (mvn compile + frontend)
echo   8. Limpiar (mvn clean + dist)
echo   0. Salir
echo.
set /p "OPTION=  Seleccione: "
if "%OPTION%"=="1" goto :buildAll
if "%OPTION%"=="2" goto :cmdBackend
if "%OPTION%"=="3" goto :cmdFrontend
if "%OPTION%"=="4" ( set "MOBILE_TARGET=apk" & goto :runMobile )
if "%OPTION%"=="5" ( set "MOBILE_TARGET=aab" & goto :runMobile )
if "%OPTION%"=="6" ( set "MOBILE_TARGET=ios" & goto :runMobile )
if "%OPTION%"=="7" goto :compileAll
if "%OPTION%"=="8" goto :cleanAll
if "%OPTION%"=="0" goto :endScript
goto :showMenu

REM ============================================================
REM Verificaciones de herramientas
REM ============================================================
:checkJava
if exist "C:\Program Files\Java\jdk-17\bin\java.exe" (
    set "JAVA_HOME=C:\Program Files\Java\jdk-17"
) else if exist "C:\Program Files\Eclipse Adoptium\jdk-17*" (
    for /d %%j in ("C:\Program Files\Eclipse Adoptium\jdk-17*") do set "JAVA_HOME=%%j"
) else if defined JAVA_HOME (
    echo %YELLOW%[WARN]%RESET% JDK 17 no encontrado en rutas estandar; usando JAVA_HOME=!JAVA_HOME!
) else (
    echo %RED%[ERROR]%RESET% JDK 17 no encontrado.
    exit /b 1
)
set "PATH=%JAVA_HOME%\bin;%PATH%"
java -version >nul 2>&1 || exit /b 1
echo %GREEN%[OK]%RESET% Java listo: %JAVA_HOME%
exit /b 0

:checkMaven
where mvn >nul 2>&1 || (
    if exist "C:\Program Files\maven\bin\mvn.cmd" set "PATH=C:\Program Files\maven\bin;%PATH%"
)
call mvn --version >nul 2>&1 || (
    echo %RED%[ERROR]%RESET% Maven no encontrado.
    exit /b 1
)
echo %GREEN%[OK]%RESET% Maven disponible.
exit /b 0

:checkNode
where node >nul 2>&1 || (
    echo %RED%[ERROR]%RESET% Node.js no encontrado.
    exit /b 1
)
for /f "delims=" %%v in ('node -v') do echo %GREEN%[OK]%RESET% Node: %%v
exit /b 0

:checkPython
where python >nul 2>&1 || (
    echo %RED%[ERROR]%RESET% Python no encontrado.
    exit /b 1
)
for /f "delims=" %%v in ('python --version') do echo %GREEN%[OK]%RESET% %%v
exit /b 0

:checkAndroidSdk
if not defined ANDROID_HOME if exist "%LOCALAPPDATA%\Android\Sdk" set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
if not defined ANDROID_HOME (
    echo %RED%[ERROR]%RESET% Android SDK no encontrado. Instale Android Studio o defina ANDROID_HOME.
    exit /b 1
)
echo %GREEN%[OK]%RESET% Android SDK: !ANDROID_HOME!
exit /b 0

REM ============================================================
REM BACKEND JAVA - microservicios Spring Boot (Maven multi-modulo)
REM ============================================================
:buildJava
set "BUILD_LOG=!BUILD_LOG_DIR!\build-java-!BUILD_LOG_TS!.log"
call :checkJava || exit /b 1
call :checkMaven || exit /b 1
echo %CYAN%[BUILD]%RESET% backend Java ^(mvn clean package: api-gateway, agro-service^)...
echo [build] Log: !BUILD_LOG!
pushd "!JAVA_DIR!"
call mvn clean package -DskipTests > "!BUILD_LOG!" 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% Fallo compilacion Java. Ver: !BUILD_LOG!
    popd
    exit /b 1
)
popd
for /d %%s in ("!JAVA_DIR!\*") do if exist "%%s\target\*.jar" echo %GREEN%[OK]%RESET% %%~nxs
exit /b 0

REM ============================================================
REM BACKEND PYTHON - un microservicio FastAPI por carpeta
REM ============================================================
:buildPython
set "BUILD_LOG=!BUILD_LOG_DIR!\build-python-!BUILD_LOG_TS!.log"
call :checkPython || exit /b 1
echo %CYAN%[BUILD]%RESET% backend Python ^(venv + requirements por servicio^)...
echo [build] Log: !BUILD_LOG!
set "PY_FAILED=0"
for /d %%s in ("!PYTHON_DIR!\*") do (
    if exist "%%s\requirements.txt" (
        pushd "%%s"
        if not exist ".venv\Scripts\python.exe" python -m venv .venv >> "!BUILD_LOG!" 2>&1
        call ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt >> "!BUILD_LOG!" 2>&1
        if errorlevel 1 (
            echo %RED%[ERROR]%RESET% %%~nxs: fallo instalando dependencias
            set "PY_FAILED=1"
        ) else (
            call ".venv\Scripts\python.exe" -c "import main" >> "!BUILD_LOG!" 2>&1
            if errorlevel 1 (
                echo %RED%[ERROR]%RESET% %%~nxs: error en main.py
                set "PY_FAILED=1"
            ) else (
                echo %GREEN%[OK]%RESET% %%~nxs
            )
        )
        popd
    )
)
if "!PY_FAILED!"=="1" exit /b 1
exit /b 0

REM ============================================================
REM FRONTEND - Vue 3 + Vite
REM ============================================================
:ensureNpmDeps
if not exist "node_modules" (
    echo %CYAN%[NPM]%RESET% node_modules no existe, instalando ^(npm ci^)...
    call npm ci >> "!BUILD_LOG!" 2>&1
    exit /b !errorlevel!
)
echo %CYAN%[NPM]%RESET% Sincronizando dependencias ^(npm install^)...
call npm install --no-audit --no-fund >> "!BUILD_LOG!" 2>&1
exit /b !errorlevel!

:buildFrontend
set "BUILD_LOG=!BUILD_LOG_DIR!\build-frontend-!BUILD_LOG_TS!.log"
call :checkNode || exit /b 1
echo %CYAN%[BUILD]%RESET% frontend ^(npm run build^)...
echo [build] Log: !BUILD_LOG!
pushd "!FRONTEND_DIR!"
call :ensureNpmDeps
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% Fallo instalando dependencias npm. Ver: !BUILD_LOG!
    popd
    exit /b 1
)
if exist "dist" rmdir /s /q "dist" >> "!BUILD_LOG!" 2>&1
call npm run build >> "!BUILD_LOG!" 2>&1
if errorlevel 1 (
    echo %RED%[ERROR]%RESET% Fallo compilacion frontend. Ver: !BUILD_LOG!
    popd
    exit /b 1
)
popd
echo %GREEN%[OK]%RESET% frontend compilado en 03. frontend\dist
exit /b 0

REM ============================================================
REM MOBILE - Capacitor 6 (empaqueta 03. frontend\dist)
REM   apk (defecto): 05. mobile\release\android\allpashift-debug.apk
REM   aab          : 05. mobile\release\android\allpashift-release.aab (sin firmar)
REM   ios          : proyecto Xcode en 05. mobile\ios + paquete de fuentes en
REM                  05. mobile\release\ios\allpashift-ios-xcode.zip
REM                  (el .ipa se compila en una Mac con Xcode)
REM ============================================================
:buildMobile
if "!MOBILE_TARGET!"=="" set "MOBILE_TARGET=apk"
call :buildFrontend || exit /b 1
set "BUILD_LOG=!BUILD_LOG_DIR!\build-mobile-!MOBILE_TARGET!-!BUILD_LOG_TS!.log"
echo %CYAN%[BUILD]%RESET% mobile !MOBILE_TARGET!...
echo [build] Log: !BUILD_LOG!
pushd "!MOBILE_DIR!"
call :ensureNpmDeps
if errorlevel 1 ( echo %RED%[ERROR]%RESET% Fallo npm en 05. mobile. Ver: !BUILD_LOG! & popd & exit /b 1 )
if /i "!MOBILE_TARGET!"=="ios" goto :mobileIos

call :checkJava || ( popd & exit /b 1 )
call :checkAndroidSdk || ( popd & exit /b 1 )
if not exist "android" (
    echo %CYAN%[CAP]%RESET% Creando proyecto Android ^(npx cap add android^)...
    call npx cap add android >> "!BUILD_LOG!" 2>&1
    if errorlevel 1 ( echo %RED%[ERROR]%RESET% Fallo cap add android. Ver: !BUILD_LOG! & popd & exit /b 1 )
)
echo %CYAN%[CAP]%RESET% Sincronizando frontend -^> Android...
call npx cap sync android >> "!BUILD_LOG!" 2>&1
if errorlevel 1 ( echo %RED%[ERROR]%RESET% Fallo cap sync. Ver: !BUILD_LOG! & popd & exit /b 1 )
if not exist "!RELEASE_ANDROID!" mkdir "!RELEASE_ANDROID!"
if /i "!MOBILE_TARGET!"=="aab" (
    echo %CYAN%[GRADLE]%RESET% Generando AAB ^(bundleRelease^)...
    call "!MOBILE_DIR!\android\gradlew.bat" -p "!MOBILE_DIR!\android" --no-daemon bundleRelease >> "!BUILD_LOG!" 2>&1
    if errorlevel 1 ( echo %RED%[ERROR]%RESET% Fallo Gradle. Ver: !BUILD_LOG! & popd & exit /b 1 )
    copy /y "!MOBILE_DIR!\android\app\build\outputs\bundle\release\app-release.aab" "!RELEASE_ANDROID!\allpashift-release.aab" >nul
    echo %GREEN%[OK]%RESET% AAB ^(sin firmar^): 05. mobile\release\android\allpashift-release.aab
) else (
    echo %CYAN%[GRADLE]%RESET% Generando APK ^(assembleDebug^)...
    call "!MOBILE_DIR!\android\gradlew.bat" -p "!MOBILE_DIR!\android" --no-daemon assembleDebug >> "!BUILD_LOG!" 2>&1
    if errorlevel 1 ( echo %RED%[ERROR]%RESET% Fallo Gradle. Ver: !BUILD_LOG! & popd & exit /b 1 )
    copy /y "!MOBILE_DIR!\android\app\build\outputs\apk\debug\app-debug.apk" "!RELEASE_ANDROID!\allpashift-debug.apk" >nul
    echo %GREEN%[OK]%RESET% APK listo: 05. mobile\release\android\allpashift-debug.apk
)
popd
exit /b 0

:mobileIos
if not exist "ios" (
    echo %CYAN%[CAP]%RESET% Creando proyecto iOS ^(npx cap add ios^)...
    call npx cap add ios >> "!BUILD_LOG!" 2>&1
    if not exist "ios\App" ( echo %RED%[ERROR]%RESET% Fallo cap add ios. Ver: !BUILD_LOG! & popd & exit /b 1 )
)
echo %CYAN%[CAP]%RESET% Copiando frontend -^> iOS ^(npx cap copy ios^)...
call npx cap copy ios >> "!BUILD_LOG!" 2>&1
if errorlevel 1 ( echo %RED%[ERROR]%RESET% Fallo cap copy ios. Ver: !BUILD_LOG! & popd & exit /b 1 )
if not exist "!RELEASE_IOS!" mkdir "!RELEASE_IOS!"
powershell -NoProfile -Command "Compress-Archive -Path '!MOBILE_DIR!\ios\App' -DestinationPath '!RELEASE_IOS!\allpashift-ios-xcode.zip' -Force" >> "!BUILD_LOG!" 2>&1
popd
echo %GREEN%[OK]%RESET% Proyecto Xcode: 05. mobile\release\ios\allpashift-ios-xcode.zip
echo %YELLOW%[INFO]%RESET% El .ipa se compila en una Mac: abrir ios\App\App.xcworkspace ^> Product ^> Archive
exit /b 0

REM ============================================================
REM Comandos
REM ============================================================
:buildAll
call :buildJava || set "BUILD_FAILED=1"
call :buildPython || set "BUILD_FAILED=1"
call :buildFrontend || set "BUILD_FAILED=1"
goto :summary

:cmdBackend
call :buildJava || set "BUILD_FAILED=1"
call :buildPython || set "BUILD_FAILED=1"
goto :summary

:cmdJava
call :buildJava || set "BUILD_FAILED=1"
goto :summary

:cmdPython
call :buildPython || set "BUILD_FAILED=1"
goto :summary

:cmdFrontend
call :buildFrontend || set "BUILD_FAILED=1"
goto :summary

:cmdMobile
set "MOBILE_TARGET=%~2"
:runMobile
call :buildMobile || set "BUILD_FAILED=1"
goto :summary

:compileAll
set "BUILD_LOG=!BUILD_LOG_DIR!\compile-!BUILD_LOG_TS!.log"
call :checkJava || goto :endScript
call :checkMaven || goto :endScript
echo %CYAN%[INFO]%RESET% Compilacion rapida Java ^(mvn compile^)...
pushd "!JAVA_DIR!"
call mvn compile -q > "!BUILD_LOG!" 2>&1
if errorlevel 1 set "BUILD_FAILED=1"
popd
call :buildFrontend || set "BUILD_FAILED=1"
goto :summary

:testAll
call :checkJava || goto :endScript
call :checkMaven || goto :endScript
pushd "!JAVA_DIR!"
call mvn test
if errorlevel 1 set "BUILD_FAILED=1"
popd
goto :summary

:cleanAll
call :checkMaven || goto :endScript
pushd "!JAVA_DIR!"
call mvn -q clean
popd
if exist "!FRONTEND_DIR!\dist" rmdir /s /q "!FRONTEND_DIR!\dist"
echo %GREEN%[OK]%RESET% Limpieza completada.
goto :endScript

:summary
echo.
if "!BUILD_FAILED!"=="1" (
    echo %RED%========== BUILD CON ERRORES - revisar build-logs\ ==========%RESET%
) else (
    echo %GREEN%========== BUILD OK ==========%RESET%
)
goto :endScript

:showHelp
echo.
echo %CYAN%Uso:%RESET% build.bat ^<comando^>
echo.
echo   (sin argumentos) / all   backend + frontend
echo   backend                  Java (api-gateway, agro-service) + Python (microservicios)
echo   java / python            solo una parte del backend
echo   frontend                 Vue: npm install + npm run build
echo   mobile [apk^|aab^|ios]     app movil Capacitor (por defecto: apk)
echo                              apk  -^> 05. mobile\release\android\allpashift-debug.apk
echo                              aab  -^> 05. mobile\release\android\allpashift-release.aab
echo                              ios  -^> 05. mobile\release\ios\allpashift-ios-xcode.zip
echo   compile                  validacion rapida: mvn compile + frontend
echo   test                     mvn test (Java)
echo   clean                    mvn clean + borrar dist
echo   menu / help
echo.
goto :endScript

:endScript
for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "SCRIPT_END_HUMAN=%%t"
echo [build] Fin: !SCRIPT_END_HUMAN!
set "RC=!BUILD_FAILED!"
endlocal & exit /b %RC%
