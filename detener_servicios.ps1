# Script para DETENER todos los servicios
# Mata los procesos en puertos 8000 y 5173

Write-Host "================================================" -ForegroundColor Red
Write-Host "   DETENIENDO SERVICIOS (Matando procesos...)" -ForegroundColor Red
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
                taskkill /F /PID $p | Out-Null
                Write-Host " OK." -ForegroundColor Green
            }
            catch {
                Write-Host " ERROR: $_" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host " Nada corriendo (Libre)." -ForegroundColor Gray
    }
}

Kill-Port 8000
Kill-Port 5173

Write-Host "`n------------------------------------------------"
Write-Host "Servicios Detenidos." -ForegroundColor Cyan
