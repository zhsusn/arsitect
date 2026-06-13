@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "DB_FILE=%SCRIPT_DIR%..\backend\data\sdlc-visualizer.db"

echo ============================================
echo   Arsitect SDLC Visualizer - 重置数据库
echo ============================================
echo.

echo [1/2] 正在停止开发服务...
call "%SCRIPT_DIR%stop-dev.bat" >nul 2>&1
timeout /T 3 /NOBREAK >nul

echo [2/2] 正在删除数据库文件...
if exist "%DB_FILE%" (
    del /F /Q "%DB_FILE%" >nul 2>&1
    if exist "%DB_FILE%" (
        echo [错误] 无法删除数据库文件，可能仍有进程占用。
        echo 请手动结束占用该文件的进程后重试：
        echo   %DB_FILE%
    ) else (
        echo 已删除：%DB_FILE%
        echo.
        echo 请重新运行 scripts\start-dev.bat 启动服务，数据库将按最新模型自动重建。
    )
) else (
    echo 数据库文件不存在：%DB_FILE%
    echo 重启后端时会自动创建。
)

endlocal
pause
