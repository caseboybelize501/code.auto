@echo off
REM JARVIS - llama.cpp Server Startup Script
REM Usage: start_llama_server.bat [model_name] [port]
REM 
REM Examples:
REM   start_llama_server.bat                        - Uses default model
REM   start_llama_server.bat qwen2.5-coder-7b       - Uses specified model
REM   start_llama_server.bat qwen3-coder-30b-q4     - Uses 30B quantized model
REM   start_llama_server.bat mistral-7b 8081        - Uses custom port

setlocal enabledelayedexpansion

REM Default settings
set DEFAULT_MODEL=D:\models\qwen2.5-coder-7b.gguf
set DEFAULT_PORT=8080
set CONTEXT_LENGTH=8192
set GPU_LAYERS=99

REM Parse arguments
set MODEL_PATH=%DEFAULT_MODEL%
set PORT=%DEFAULT_PORT%

if not "%~1"=="" (
    if "%~1"=="qwen2.5-coder-7b" set MODEL_PATH=D:\models\qwen2.5-coder-7b.gguf
    if "%~1"=="qwen3-coder-30b-q4" set MODEL_PATH=D:\models\qwen3-coder-30b-q4.gguf
    if "%~1"=="qwen3-coder-30b" set MODEL_PATH=D:\models\qwen3-coder-30b.gguf
    if "%~1"=="qwen2.5-coder-32b" set MODEL_PATH=D:\Users\CASE\models\qwen2.5-coder-32b.gguf
    if "%~1"=="qwen3.5-9b" set MODEL_PATH=D:\Users\CASE\models\qwen3.5-9b.gguf
    if "%~1"=="qwen3.5-27b" set MODEL_PATH=D:\Users\CASE\models\qwen3.5-27b.gguf
    if "%~1"=="qwen3.5-35b" set MODEL_PATH=D:\Users\CASE\models\qwen3.5-35b.gguf
    if "%~1"=="qwen3.5-35b-a3b" set MODEL_PATH=D:\Users\CASE\models\qwen3.5-35b-a3b.gguf
    if "%~1"=="glm-4.7-flash" set MODEL_PATH=D:\Users\CASE\models\glm-4.7-flash.gguf
    if "%~1"=="nemotron-30b" set MODEL_PATH=D:\Users\CASE\models\nemotron-3-nano-30b.gguf
    if "%~1"=="mistral-7b" set MODEL_PATH=D:\AI\models\mistral-7b-instruct-v0.2.Q4_K_M.gguf
    if "%~1"=="mistral-small-24b" set MODEL_PATH=D:\Users\CASE\AppData\Roaming\Block\goose\data\models\Mistral-Small-24B-Instruct-2501-Q4_K_M.gguf
    if "%~1"=="qwen3-coder-30b-instruct-q8" set MODEL_PATH=D:\Users\CASE\AppData\Roaming\Block\goose\data\models\Qwen3-Coder-30B-A3B-Instruct-Q8_0.gguf
    if "%~1"=="nomic-embed" set MODEL_PATH=D:\Users\CASE\.lmstudio\.internal\bundled-models\nomic-ai\nomic-embed-text-v1.5-GGUF\nomic-embed-text-v1.5.Q4_K_M.gguf
)

if not "%~2"=="" set PORT=%~2

REM Check if model file exists
if not exist "%MODEL_PATH%" (
    echo ERROR: Model file not found: %MODEL_PATH%
    echo.
    echo Available models:
    echo   qwen2.5-coder-7b          - Qwen2.5 Coder 7B (default, recommended for code)
    echo   qwen3-coder-30b-q4        - Qwen3 Coder 30B quantized
    echo   qwen2.5-coder-32b         - Qwen2.5 Coder 32B
    echo   qwen3.5-9b                - Qwen3.5 9B (fast)
    echo   qwen3.5-27b               - Qwen3.5 27B
    echo   qwen3.5-35b               - Qwen3.5 35B
    echo   qwen3.5-35b-a3b           - Qwen3.5 35B A3B
    echo   glm-4.7-flash             - GLM-4.7 Flash
    echo   nemotron-30b              - Nemotron-3 Nano 30B
    echo   mistral-7b                - Mistral 7B Instruct
    echo   mistral-small-24b         - Mistral Small 24B Instruct
    echo   qwen3-coder-30b-instruct-q8 - Qwen3 Coder 30B Instruct Q8
    echo   nomic-embed               - Nomic Embed (embedding model)
    exit /b 1
)

echo ============================================
echo   JARVIS - llama.cpp Server
echo ============================================
echo.
echo Starting llama.cpp server...
echo   Model: %MODEL_PATH%
echo   Port:  %PORT%
echo   Context Length: %CONTEXT_LENGTH%
echo   GPU Layers: %GPU_LAYERS%
echo.
echo Press Ctrl+C to stop the server
echo ============================================
echo.

REM Start the server
python -m llama_cpp.server --model "%MODEL_PATH%" --port %PORT% --ctx-size %CONTEXT_LENGTH% --n-gpu-layers %GPU_LAYERS% --host 0.0.0.0
