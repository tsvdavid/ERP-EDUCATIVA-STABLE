
import os
import sys
import django

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, Institution
from health.models import MedicalRecord
from treasury.models import PaymentConcept
from helpdesk.models import ServiceCatalog
from rest_framework.test import APIRequestFactory, force_authenticate
from health.views import MedicalRecordViewSet
from treasury.views import PaymentConceptViewSet
from helpdesk.views import ServiceCatalogViewSet

def verify_isolation():
    print("🛡️ >>> INICIANDO VERIFICACIÓN DE SEGURIDAD (AISLAMIENTO MULTI-TENANT) <<<")
    
    # 1. Identificar Instituciones y Usuarios
    inst_6 = Institution.objects.get(id=6) # Colegio Técnico Innovación
    inst_7 = Institution.objects.get(id=7) # Unidad Educativa Luz del Saber
    
    teacher_6 = User.objects.filter(role='TEACHER', institution=inst_6).first()
    
    # 2. Verificar MedicalRecord
    print(f"\n🩺 Probando aislamiento en Salud (MedicalRecord):")
    total_records = MedicalRecord.objects.count()
    records_inst7 = MedicalRecord.objects.filter(student__institution=inst_7).count()
    print(f"   - Total records en DB: {total_records}")
    print(f"   - Records de Inst 7: {records_inst7}")
    
    factory = APIRequestFactory()
    request = factory.get('/api/health/medical-records/')
    force_authenticate(request, user=teacher_6)
    
    view = MedicalRecordViewSet.as_view({'get': 'list'})
    response = view(request)
    
    visible_count = len(response.data)
    print(f"   - Records visibles para Profesor Inst 6: {visible_count}")
    
    leaks = [r for r in response.data if r['student_details']['institution'] != 6]
    if visible_count > 0 and len(leaks) == 0:
        print("   ✅ AISLAMIENTO EXITOSO: Solo ve registros de su propia institución.")
    elif visible_count == 0:
        print("   ⚠️  ADVERTENCIA: No se ven registros (¿no hay datos para Inst 6?).")
    else:
        print(f"   ❌ ERROR DE SEGURIDAD: Se filtraron {len(leaks)} registros de otras instituciones.")

    # 3. Verificar Treasury (PaymentConcept)
    print(f"\n💰 Probando aislamiento en Tesorería (PaymentConcept):")
    request_pay = factory.get('/api/treasury/concepts/')
    force_authenticate(request_pay, user=teacher_6)
    view_pay = PaymentConceptViewSet.as_view({'get': 'list'})
    response_pay = view_pay(request_pay)
    
    visible_pay = len(response_pay.data)
    leaks_pay = [r for r in response_pay.data if r['institution'] != 6]
    print(f"   - Conceptos visibles para Profesor Inst 6: {visible_pay}")
    if len(leaks_pay) == 0:
        print("   ✅ AISLAMIENTO EXITOSO: Tesorería protegida.")
    else:
        print(f"   ❌ ERROR DE SEGURIDAD: Tesorería expuesta ({len(leaks_pay)} filtrados).")

    # 4. Verificar Helpdesk (ServiceCatalog)
    print(f"\n🎫 Probando aislamiento en Helpdesk (ServiceCatalog):")
    request_hd = factory.get('/api/helpdesk/catalog/')
    force_authenticate(request_hd, user=teacher_6)
    view_hd = ServiceCatalogViewSet.as_view({'get': 'list'})
    response_hd = view_hd(request_hd)
    
    visible_hd = len(response_hd.data)
    leaks_hd = [r for r in response_hd.data if r['institution'] != 6]
    print(f"   - Items de catálogo visibles: {visible_hd}")
    if len(leaks_hd) == 0:
        print("   ✅ AISLAMIENTO EXITOSO: Helpdesk protegido.")
    else:
        print(f"   ❌ ERROR DE SEGURIDAD: Helpdesk expuesto.")

    # 5. Verificar Academic (Course)
    print(f"\n📚 Probando aislamiento en Académico (Course):")
    from academic.views import CourseViewSet
    request_ac = factory.get('/api/academic/courses/')
    force_authenticate(request_ac, user=teacher_6)
    view_ac = CourseViewSet.as_view({'get': 'list'})
    response_ac = view_ac(request_ac)
    
    visible_ac = len(response_ac.data)
    leaks_ac = [r for r in response_ac.data if r['institution'] != 6]
    print(f"   - Cursos visibles: {visible_ac}")
    if len(leaks_ac) == 0:
        print("   ✅ AISLAMIENTO EXITOSO: Académico protegido.")
    else:
        print(f"   ❌ ERROR DE SEGURIDAD: Académico expuesto.")

    print("\n🏁 >>> VERIFICACIÓN COMPLETADA <<<")

if __name__ == "__main__":
    verify_isolation()
