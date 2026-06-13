# Arsitect SDLC Visualizer - 开发环境启动脚本 (PowerShell)
$ErrorActionPreference = "Continue"

$rootDir = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $rootDir "backend"
$frontendDir = Join-Path $rootDir "frontend"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Arsitect SDLC Visualizer - 开发环境启动" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Seed demo data
Write-Host "[1/4] 初始化演示数据..." -ForegroundColor Yellow
& python (Join-Path $PSScriptRoot "seed_demo.py")
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] 数据初始化遇到问题，继续启动..." -ForegroundColor DarkYellow
}
Write-Host ""

# Step 2: Start backend
Write-Host "[2/4] 启动后端服务 (http://localhost:8000)..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    python main.py
} -ArgumentList $backendDir

# Step 3: Start frontend
Write-Host "[3/4] 启动前端服务 (http://localhost:5173)..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    npm run dev
} -ArgumentList $frontendDir

# Step 4: Wait and check
Write-Host "[4/4] 等待服务就绪..." -ForegroundColor Yellow
$maxWait = 30
$backendReady = $false
$frontendReady = $false
for ($i = 0; $i -lt $maxWait; $i++) {
    Start-Sleep -Seconds 1

    # Check backend
    if (-not $backendReady) {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) {
                $backendReady = $true
                Write-Host "      后端已就绪 ✓" -ForegroundColor Green
            }
        } catch {}
    }

    # Check frontend (Vite dev server responds with 200 on root)
    if (-not $frontendReady) {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) {
                $frontendReady = $true
                Write-Host "      前端已就绪 ✓" -ForegroundColor Green
            }
        } catch {}
    }

    if ($backendReady -and $frontendReady) { break }
}

if ($backendReady -and $frontendReady) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "   服务已启动！" -ForegroundColor Green
    Write-Host ""
    Write-Host "   前端页面 : http://localhost:5173"
    Write-Host "   API 文档 : http://localhost:8000/docs"
    Write-Host "   演示数据 : 应用=demo-app-001 / 项目=demo-project-001"
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Start-Process "http://localhost:5173"
} else {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    if (-not $backendReady) { Write-Host "   [错误] 后端未能在 ${maxWait}s 内就绪" -ForegroundColor Red }
    if (-not $frontendReady) { Write-Host "   [错误] 前端未能在 ${maxWait}s 内就绪" -ForegroundColor Red }
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "后端日志:" -ForegroundColor Yellow
    Receive-Job -Job $backendJob
    Write-Host ""
    Write-Host "前端日志:" -ForegroundColor Yellow
    Receive-Job -Job $frontendJob
}

Write-Host ""
Write-Host "按 Enter 停止服务并退出..." -ForegroundColor Cyan
$null = Read-Host

# Cleanup
Write-Host "正在停止服务..." -ForegroundColor Yellow
Stop-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
Remove-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
Write-Host "服务已停止。" -ForegroundColor Green
