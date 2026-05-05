import psycopg2
import sys

def attack():
    conn_params = {
        "dbname": "erp_educativa",
        "user": "eduka_user",
        "password": "eduka_secure_2024",
        "host": "db",
        "port": "5432"
    }
    
    print("--- INICIANDO VECTOR DE ATAQUE RLS DIRECTO (POSTGRESQL) ---")
    
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # 0. VERIFICACIÓN DE IDENTIDAD
        cur.execute("SELECT current_user;")
        user = cur.fetchone()[0]
        print(f"[*] Conectado como: {user}")
        
        # Resetear cualquier configuración previa de la sesión
        cur.execute("RESET ALL;")
        
        # 1. ATAQUE SIN CONTEXTO
        print("\n[TEST 1] Intento de lectura global (SELECT * sin SET)")
        try:
            cur.execute("SELECT count(*) FROM accounting_journalentry;")
            count = cur.fetchone()[0]
            if count > 0:
                print(f"❌ FALLO DE SEGURIDAD: Se detectaron {count} registros accesibles sin tenant_id.")
            else:
                print("✅ ÉXITO: 0 registros visibles o acceso denegado.")
        except Exception as e:
            print(f"✅ ÉXITO: La consulta falló como se esperaba: {str(e).strip()}")
            conn.rollback() # Limpiar estado de error

        # 2. ATAQUE DE ELEVACIÓN (SET a Tenant 1)
        print("\n[TEST 2] Lectura con contexto legítimo (SET app.current_tenant = 1)")
        cur.execute("SET app.current_tenant = '1';")
        cur.execute("SELECT count(*) FROM accounting_journalentry;")
        count_inst1 = cur.fetchone()[0]
        print(f"   Registros visibles para Inst 1: {count_inst1}")

        # 3. ATAQUE DE ACCESO CRUZADO (Contexto 2 + Lectura ID de 1)
        print("\n[TEST 3] Ataque de acceso cruzado (SET tenant = 2, intentado leer ID de 1)")
        cur.execute("SET app.current_tenant = '2';")
        cur.execute("SELECT count(*) FROM accounting_journalentry WHERE institution_id = 1;")
        count_cross = cur.fetchone()[0]
        
        if count_cross > 0:
            print(f"❌ FALLO DE SEGURIDAD: Se detectaron {count_cross} registros de Inst 1 visibles desde Inst 2.")
        else:
            print("✅ ÉXITO: El motor de DB bloqueó el acceso cruzado (0 registros visibles).")

        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"⚠️ ERROR CRÍTICO EN EL SCRIPT: {e}")

if __name__ == "__main__":
    attack()
