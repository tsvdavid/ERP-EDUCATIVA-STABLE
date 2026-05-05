# Script para iniciar todos los servicios del ERP
# 1. Base de Datos (Docker)
# 2. Backend (Django)
# 3. Frontend (React)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   INICIANDO SISTEMA ERP EDUCATIVA" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

$RootPath = $PSScriptRoot
$BackendPath = Join-Path $RootPath "backend"
$FrontendPath = Join-Path $RootPath "frontend"

# 1. Docker
Write-Host "`n[1/3] Verificando Base de Datos (Docker)..." -ForegroundColor Yellow
Set-Location $RootPath
try {
    docker-compose up -d
    Write-Host "Docker ejecutándose." -ForegroundColor Green
}
catch {
    Write-Host "Nota: Si Docker no está instalado o falló, asegúrese de tener PostgreSQL local o Docker Desktop corriendo." -ForegroundColor Gray
}

# 2. Backend
Write-Host "`n[2/3] Iniciando Servidor Backend (Puerto 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {
    $host.UI.RawUI.WindowTitle = 'ERP Backend (Django)';
    Write-Host 'Iniciando Django...' -ForegroundColor Cyan;
    cd '$BackendPath'; 
    if (Test-Path 'venv') { .\venv\Scripts\activate }
    python manage.py runserver 0.0.0.0:8000
}"

# 3. Frontend
Write-Host "`n[3/3] Iniciando Servidor Frontend (Puerto 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {
    $host.UI.RawUI.WindowTitle = 'ERP Frontend (React)';
    Write-Host 'Iniciando React...' -ForegroundColor Cyan;
    cd '$FrontendPath'; 
    npm run dev
}"

Write-Host "`n================================================" -ForegroundColor Green
Write-Host "   SISTEMA INICIADO" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Admin:    http://localhost:8000/admin"


