import os
import django
import sys
import json
from decimal import Decimal

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from accounting.views import ReportViewSet
from rest_framework.test import APIRequestFactory, force_authenticate

def debug_report():
    print("=== DEBUG REPORTE BALANCE GENERAL ===")
    
    # Get Admin User
    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        print("No admin user found.")
        return

    print(f"Usuario: {admin.username} ({admin.email})")
    print(f"Institución: {admin.institution}")

    # Instantiate ViewSet
    view = ReportViewSet()
    
    # Mock Request
    factory = APIRequestFactory()
    request = factory.get('/api/accounting/reports/balance_sheet/')
    request.user = admin # Explicitly set user
    force_authenticate(request, user=admin)
    view.request = request
    
    # Call method
    try:
        response = view.balance_sheet(request)
        data = response.data
        
        print("\n--- Respuesta del Balance General ---")
        keys = list(data.keys())
        print(f"Keys: {keys}")
        
        print(f"Total Assets: {data.get('total_assets')} (Type: {type(data.get('total_assets'))})")
        print(f"Total Liabilities: {data.get('total_liabilities')} (Type: {type(data.get('total_liabilities'))})")
        print(f"Total Equity: {data.get('total_equity')}")
        
    except Exception as e:
        print(f"ERROR ejecutando vista: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_report()
