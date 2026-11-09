@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"

echo.
echo Preparando datos ficticios de evaluacion...
echo.

pushd "%~dp0backend"

uv run --locked python -m scripts.preparar_demo --init

if errorlevel 1 (
    popd
    echo.
    echo ERROR: No se pudieron preparar los datos.
    pause
    exit /b 1
)

popd

call "%~dp0iniciar-mesa-ayuda-demo.bat"
