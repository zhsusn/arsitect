@echo off
chcp 65001 >nul

REM Resolve paths
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
set "BACKEND_DIR=%ROOT_DIR%\backend"
set "FRONTEND_DIR=%ROOT_DIR%\frontend"
set "PIDS_DIR=%SCRIPT_DIR%.pids"

REM Ensure PID directory exists
if not exist "%PIDS_DIR%" mkdir "%PIDS_DIR%"
REM Clean up stale PID files
if exist "%PIDS_DIR%\backend.pid" del /F /Q "%PIDS_DIR%\backend.pid" >nul 2>&1
if exist "%PIDS_DIR%\frontend.pid" del /F /Q "%PIDS_DIR%\frontend.pid" >nul 2>&1

echo ============================================
echo   Arsitect SDLC Visualizer - 开发环境启动
echo ============================================
echo.

REM Step 1: Seed demo data
echo [1/6] 初始化演示数据...
python "%SCRIPT_DIR%seed_demo.py"
if errorlevel 1 (
    echo [警告] 数据初始化遇到问题，继续启动...
)
echo.

REM Step 2: Start backend (use /D to set working dir reliably)
echo [2/6] 启动后端服务 (http://localhost:8000)...
start "Backend - SDLC API" /D "%BACKEND_DIR%" cmd /k "python main.py"
echo.

REM Step 3: Record backend PID
echo [3/6] 记录后端进程 PID...
timeout /t 1 /nobreak >nul
for /f "tokens=2 delims=," %%a in ('tasklist /FI "WINDOWTITLE eq Backend - SDLC API" /FO CSV /NH 2^>nul') do (
    echo %%a > "%PIDS_DIR%\backend.pid"
    echo   后端控制台 PID=%%a
)
echo.

REM Step 4: Start frontend
echo [4/6] 启动前端服务 (http://localhost:5173)...
start "Frontend - SDLC UI" /D "%FRONTEND_DIR%" cmd /k "npm run dev"
echo.

REM Step 5: Record frontend PID
echo [5/6] 记录前端进程 PID...
timeout /t 1 /nobreak >nul
for /f "tokens=2 delims=," %%a in ('tasklist /FI "WINDOWTITLE eq Frontend - SDLC UI" /FO CSV /NH 2^>nul') do (
    echo %%a > "%PIDS_DIR%\frontend.pid"
    echo   前端控制台 PID=%%a
)
echo.

REM Step 6: Wait and open browser
echo [6/6] 等待服务就绪...
timeout /t 4 /nobreak >nul
start http://localhost:5173
echo.
echo ============================================
echo   服务已启动！
echo.
echo   前端页面 : http://localhost:5173
echo   API 文档 : http://localhost:8000/docs
echo   演示数据 : 应用=demo-app-001 / 项目=demo-project-001
echo ============================================
echo.
echo 提示：
echo   - 前后端各有一个独立的黑色窗口在运行
echo   - 关闭本窗口不会影响服务
echo   - 验证时用 stop-dev.bat 关闭服务
echo.
pause
