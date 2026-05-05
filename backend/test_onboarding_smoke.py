import os
import django
import sys

# Setup Django environment
sys.path.append('/var/www/erpeducativa/ERP-EDUCATIVA/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Institution
from users.services import InstitutionBootstrapService
from accounting.models import Account, AccountingConfig, FiscalYear
from treasury.models import PaymentMethod

def test_bootstrap():
    import uuid
    inst_name = f"Test Bootstrap {uuid.uuid4().hex[:6]}"
    
    data = {
        'name': inst_name,
        'ruc': '1799999999001'
    }
    
    print(f"Creating and bootstrapping: {inst_name}")
    try:
        institution = InstitutionBootstrapService.create_and_bootstrap(data)
        print(f"SUCCESS: Institution created with ID {institution.id}")
        
        # Validation
        print("Validating components...")
        
        # 1. Setup Status
        assert institution.setup_status == 'READY_MINIMAL', f"Expected READY_MINIMAL, got {institution.setup_status}"
        assert institution.setup_completed_at is not None, "setup_completed_at should be set"
        
        # 2. Fiscal Year
        fy = FiscalYear.objects.filter(institution=institution).count()
        print(f"Fiscal Years: {fy}")
        assert fy == 1
        
        # 3. Chart of Accounts
        acc_count = Account.objects.filter(institution=institution).count()
        print(f"Accounts created: {acc_count}")
        assert acc_count >= 30, f"Expected >= 30 accounts, got {acc_count}"
        
        # 4. Configs
        config_count = AccountingConfig.objects.filter(institution=institution).count()
        print(f"Configs created: {config_count}")
        assert config_count == 10
        
        # 5. Payment Methods
        pm_count = PaymentMethod.objects.filter(institution=institution).count()
        print(f"Payment Methods created: {pm_count}")
        assert pm_count == 2
        
        print("\nSMOKE TEST PASSED! The institution is ready for use.")
        
    except Exception as e:
        print(f"\nSMOKE TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_bootstrap()
