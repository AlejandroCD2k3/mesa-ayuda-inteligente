@echo off
setlocal
title Mesa de Ayuda UNAD IA 360

cd /d "%~dp0"

echo.
echo ================================================
echo      MESA DE AYUDA INTELIGENTE UNAD IA 360
echo ================================================
echo.

rem Verificar archivos del proyecto

if not exist "backend\app\main.py" (
    echo ERROR: No se encontro el backend.
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo ERROR: No se encontro el frontend.
    pause
    exit /b 1
)

rem Verificar herramientas necesarias

where uv >nul 2>&1

if errorlevel 1 (
    echo ERROR: uv no esta instalado o no esta en PATH.
    pause
    exit /b 1
)

where npm >nul 2>&1

if errorlevel 1 (
    echo ERROR: Node.js/npm no esta instalado o no esta en PATH.
    pause
    exit /b 1
)

rem Instalar dependencias del frontend solo si faltan

if not exist "frontend\node_modules\.bin\ng.cmd" (
    echo Instalando dependencias de Angular...

    pushd "frontend"

    call npm ci

    if errorlevel 1 (
        popd
        echo ERROR: No se pudieron instalar las dependencias.
        pause
        exit /b 1
    )

    popd
)

rem Iniciar FastAPI

echo [1/3] Iniciando FastAPI...

start "UNAD IA 360 - Backend" /D "%~dp0backend" cmd /k "uv run --locked python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

rem Iniciar Angular

echo [2/3] Iniciando Angular...

start "UNAD IA 360 - Frontend" /D "%~dp0frontend" cmd /k "npm start"

rem Esperar a que ambos servicios respondan

echo [3/3] Comprobando servicios...

powershell.exe -NoProfile -Command "$ready=$false; for($i=0; $i -lt 60; $i++){ try { $api=Invoke-WebRequest 'http://127.0.0.1:8000/api/health' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop; $web=Invoke-WebRequest 'http://127.0.0.1:4200/' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop; if($api.StatusCode -eq 200 -and $web.StatusCode -eq 200){ $ready=$true; break } } catch {} Start-Sleep -Seconds 1 }; if($ready){exit 0}else{exit 1}"

if errorlevel 1 (
    echo.
    echo No se pudo confirmar el inicio de ambos servicios.
    echo Revisa las ventanas del backend y frontend.
    pause
    exit /b 1
)

rem Abrir navegador

echo.
echo Aplicacion disponible en:
echo http://localhost:4200
echo.

start "" "http://localhost:4200/"

echo Inicio completado.
exit /b 0
