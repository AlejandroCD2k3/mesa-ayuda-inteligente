@echo off
setlocal DisableDelayedExpansion

set "ROOT=%~dp0"

if not exist "%ROOT%backend\.env" (
    echo ERROR: Falta backend\.env
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in ("%ROOT%backend\.env") do (
    if /I "%%A"=="LLM_API_KEY" set "LLM_API_KEY=%%B"
    if /I "%%A"=="LLM_MODEL" set "LLM_MODEL=%%B"
    if /I "%%A"=="LLM_BASE_URL" set "LLM_BASE_URL=%%B"
)

if not defined LLM_API_KEY (
    echo ERROR: No existe la clave LLM.
    exit /b 1
)

echo Iniciando Mesa de Ayuda Inteligente con IA...
call "%ROOT%iniciar-mesa-ayuda.bat"