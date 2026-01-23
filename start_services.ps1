# Script para iniciar/reiniciar TODOS los servicios de ERP EDUCATIVA

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   INICIANDO SISTEMA ERP EDUCATIVA COMPLETO" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Definir rutas relativas
$RootPath = $PSScriptRoot
$BackendPath = Join-Path $RootPath "backend"
$FrontendPath = Join-Path $RootPath "frontend"

# 1. Iniciar Docker Containers
Write-Host "`n[1/3] Verificando Docker y Base de Datos..." -ForegroundColor Yellow
Set-Location $RootPath

# Verificar si Docker está corriendo
$dockerRunning = $false
try {
    docker info | Out-Null
    $dockerRunning = $true
}
catch {
    $dockerRunning = $false
}

if (-not $dockerRunning) {
    Write-Host "ERROR CRÍTICO: Docker Desktop no parece estar ejecutándose." -ForegroundColor Red
    Write-Host "Por favor, inicie Docker Desktop y espere a que el icono deje de animarse." -ForegroundColor Gray
    Write-Host "Presione Enter una vez que Docker esté listo para intentar levantarlo..." -ForegroundColor Yellow
    Read-Host
    
    # Re-intentar chequeo
    try {
        docker info | Out-Null
        $dockerRunning = $true
    }
    catch {
        Write-Host "Aún no se detecta Docker. El script continuará, pero es probable que falle." -ForegroundColor Red
    }
}

try {
    Write-Host "Levantando contenedores (Solo DB)..." -ForegroundColor Cyan
    # Solo levantamos 'db' (y sus dependencias como redis si hubiese) para evitar
    # que docker levante 'backend' y ocupe el puerto 8000 que necesitamos localmente.
    docker-compose up -d db
    Write-Host "Contenedores iniciados." -ForegroundColor Green
}
catch {
    Write-Host "Error al ejecutar docker-compose." -ForegroundColor Red
}

# Esperar robustamente a que el puerto 5432 esté escuchando
Write-Host "Esperando a que la base de datos esté lista en el puerto 5432 (127.0.0.1)..." -ForegroundColor Yellow
$maxRetries = 40
$retryCount = 0
$portReady = $false

while (-not $portReady -and $retryCount -lt $maxRetries) {
    try {
        # Usamos 127.0.0.1 explícitamente para evitar problemas con ::1 (IPv6)
        $connection = Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -WarningAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            $portReady = $true
            Write-Host "`n¡Base de datos accesible!" -ForegroundColor Green
        }
        else {
            Write-Host "." -NoNewline -ForegroundColor Gray
            Start-Sleep -Seconds 1
            $retryCount++
        }
    }
    catch {
        Write-Host "." -NoNewline -ForegroundColor Gray
        Start-Sleep -Seconds 1
        $retryCount++
    }
}

if (-not $portReady) {
    Write-Host "`nADVERTENCIA: La base de datos no respondió en el puerto 5432 después de $($maxRetries) segundos." -ForegroundColor Red
    Write-Host "Es posible que el backend falle al conectar." -ForegroundColor Red
    Read-Host "Presione Enter para continuar de todos modos..."
}
else {
    Write-Host " OK."
}

# 2. Iniciar Backend (Django)
Write-Host "`n[2/3] Levantando Backend (Django)..." -ForegroundColor Yellow
# Usamos Start-Process para abrir una nueva ventana que se mantenga abierta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {
    `$host.UI.RawUI.WindowTitle = 'ERP Backend (Django)';
    Write-Host 'Iniciando Backend Django...' -ForegroundColor Cyan;
    cd '$BackendPath'; 
    try {
        if (Test-Path 'venv') {
            .\venv\Scripts\activate; 
        } else {
             Write-Host 'ADVERTENCIA: No se encontro carpeta venv. Intentando python global...' -ForegroundColor Yellow;
        }
        python manage.py runserver 0.0.0.0:8000
    } catch {
        Write-Host 'Error al iniciar backend. Verifique que el entorno virtual exista.' -ForegroundColor Red;
        Read-Host 'Presione Enter para salir...';
    }
}"

# 3. Iniciar Frontend (Vite/React)
Write-Host "`n[3/3] Levantando Frontend (React)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& {
    `$host.UI.RawUI.WindowTitle = 'ERP Frontend (React)';
    Write-Host 'Iniciando Frontend React...' -ForegroundColor Cyan;
    cd '$FrontendPath'; 
    npm run dev
}"

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "   ¡SISTEMA INICIADO!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
Write-Host "`nEsta ventana se cerrará en 10 segundos..."
Start-Sleep -Seconds 10
