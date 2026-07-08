import psycopg2
from pathlib import Path

SQL_FILE = Path(__file__).resolve().parent / 'apply_robust_rls_v3.sql'


def run_sql_file(filename):
    conn_params = {
        "dbname": "erp_educativa",
        "user": "postgres",
        "password": "postgrespw",
        "host": "localhost",
        "port": "5432"
    }
    
    try:
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cur = conn.cursor()
        
        print(f"Leyendo archivo SQL: {filename}")
        with open(filename, 'r') as f:
            sql = f.read()
            
        print("Ejecutando SQL...")
        cur.execute(sql)
        print("SQL ejecutado exitosamente.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error ejecutando SQL: {e}")

if __name__ == "__main__":
    run_sql_file(SQL_FILE)
