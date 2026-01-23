# Script para REINICIAR (Resetear) los servicios
# Mata los procesos en puertos 8000 y 5173 y vuelve a iniciar

Write-Host "================================================" -ForegroundColor Red
Write-Host "   REINICIANDO SISTEMA (Matando procesos...)" -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Red

# Función para matar proceso por puerto
function Kill-Port ($port) {
    Write-Host "Revisando puerto $port..." -NoNewline
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        Write-Host " Encontrado(s) PID: $($pids -join ', ')" -ForegroundColor Yellow
        
        foreach ($p in $pids) {
            if ($p -eq 0) { continue } # System Idle Process check
            try {
                Write-Host "   -> Intentando matar PID $p..." -NoNewline
                # Usar taskkill para asegurar fuerza
                taskkill /F /PID $p | Out-Null
                Write-Host " OK." -ForegroundColor Green
            }
            catch {
                Write-Host " ERROR: $_" -ForegroundColor Red
            }
        }
        
        # Verificación doble
        Start-Sleep -Seconds 1
        $still_alive = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($still_alive) {
            Write-Host "   ADVERTENCIA: El puerto $port parece seguir ocupado." -ForegroundColor Red
        }
        else {
            Write-Host "   Puerto $port liberado exitosamente." -ForegroundColor Cyan
        }
        
    }
    else {
        Write-Host " Nada corriendo (Libre)." -ForegroundColor Gray
    }
}

Kill-Port 8000
Kill-Port 5173

Write-Host "`n------------------------------------------------"
Write-Host "Procesos limpios. Iniciando servicios en 3 seg..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# Llamar al script de inicio principal
& "$PSScriptRoot\start_services.ps1"
