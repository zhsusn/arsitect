@echo off
setlocal enabledelayedexpansion
echo ============================================
echo   Arsitect SDLC Visualizer - 停止服务
echo ============================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PIDS_DIR=%SCRIPT_DIR%.pids"

REM Stop backend. Prefer the PID recorded by start-dev.bat; fall back to window title.
echo [1/2] 停止后端服务...
if exist "%PIDS_DIR%\backend.pid" (
    set /p BACKEND_PID=<"%PIDS_DIR%\backend.pid"
    if not "!BACKEND_PID!"=="" (
        echo   停止后端进程树，根 PID=!BACKEND_PID!
        taskkill /F /T /PID !BACKEND_PID! >nul 2>&1
    )
    del /F /Q "%PIDS_DIR%\backend.pid" >nul 2>&1
) else (
    for /f "tokens=2 delims=," %%a in ('tasklist /FI "WINDOWTITLE eq Backend - SDLC API" /FO CSV /NH 2^>nul') do (
        echo   停止后端进程树，根 PID=%%a
        taskkill /F /T /PID %%a >nul 2>&1
    )
)

REM Stop frontend. Prefer the PID recorded by start-dev.bat; fall back to window title.
echo [2/2] 停止前端服务...
if exist "%PIDS_DIR%\frontend.pid" (
    set /p FRONTEND_PID=<"%PIDS_DIR%\frontend.pid"
    if not "!FRONTEND_PID!"=="" (
        echo   停止前端进程树，根 PID=!FRONTEND_PID!
        taskkill /F /T /PID !FRONTEND_PID! >nul 2>&1
    )
    del /F /Q "%PIDS_DIR%\frontend.pid" >nul 2>&1
) else (
    for /f "tokens=2 delims=," %%a in ('tasklist /FI "WINDOWTITLE eq Frontend - SDLC UI" /FO CSV /NH 2^>nul') do (
        echo   停止前端进程树，根 PID=%%a
        taskkill /F /T /PID %%a >nul 2>&1
    )
)

echo.
echo 服务已停止。
pause
