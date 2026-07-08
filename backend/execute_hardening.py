import os
import django
from pathlib import Path
from django.db import connection

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def run_hardening():
    sql_path = Path(__file__).resolve().parent / 'apply_robust_rls_v3.sql'
    if not sql_path.exists():
        print(f"Error: {sql_path} not found")
        return

    with open(sql_path, 'r') as f:
        sql = f.read()

    print("Executing hardening SQL through Django connection...")
    with connection.cursor() as cursor:
        cursor.execute(sql)
    print("Success: Hardening applied.")

if __name__ == "__main__":
    run_hardening()
