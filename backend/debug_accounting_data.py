import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, Institution
from accounting.models import Account, JournalEntry
from purchases.models import Supplier

def debug_data():
    print("=== DIAGNÓSTICO DE DATOS CONTABLES ===")
    
    # 1. Institutions
    institutions = Institution.objects.all()
    print(f"\n1. Instituciones encontradas: {institutions.count()}")
    for inst in institutions:
        print(f"   - ID: {inst.id} | Nombre: {inst.name}")
        
        # Check data for this institution
        acc_count = Account.objects.filter(institution=inst).count()
        journal_count = JournalEntry.objects.filter(institution=inst).count()
        supplier_count = Supplier.objects.filter(institution=inst).count()
        print(f"     -> Cuentas: {acc_count} | Asientos: {journal_count} | Proveedores: {supplier_count}")

    # 2. Check Admin User
    print("\n2. Verificando Usuario 'admin' (u otro superusuario)")
    admins = User.objects.filter(is_superuser=True)
    if not admins.exists():
        print("   [!] No se encontraron superusuarios.")
    
    for admin in admins:
        print(f"   - Usuario: {admin.username} | ID: {admin.id}")
        if admin.institution:
            print(f"     -> Institución Asignada: {admin.institution.name} (ID: {admin.institution.id})")
        else:
            print(f"     -> [ERROR] Institución Asignada: NINGUNA (None)")
            
            # ATTEMPT FIX
            if institutions.exists():
                target_inst = institutions.first()
                print(f"     -> [CORRIGIENDO] Asignando Institución ID {target_inst.id} a {admin.username}...")
                admin.institution = target_inst
                admin.save()
                print("     -> [OK] Corrección aplicada. Por favor recarga la página.")
            else:
                print("     -> [ERROR] No hay instituciones para asignar.")

    # 3. Check Academic Data (Students/Teachers)
    print("\n3. Verificando Datos Académicos")
    from academic.models import Course, Subject
    
    users_count = User.objects.count()
    students = User.objects.filter(role='STUDENT')
    teachers = User.objects.filter(role='TEACHER')
    courses = Course.objects.all()
    
    print(f"   - Total Usuarios: {users_count}")
    print(f"   - Estudiantes: {students.count()}")
    print(f"   - Profesores: {teachers.count()}")
    print(f"   - Cursos: {courses.count()}")
    
    # Check linkage
    orphaned_students = students.filter(institution__isnull=True).count()
    orphaned_courses = courses.filter(institution__isnull=True).count()
    
    if orphaned_students > 0 or orphaned_courses > 0:
        print(f"   [!] ALERTA: Hay {orphaned_students} estudiantes y {orphaned_courses} cursos SIN institución.")
        
        if institutions.exists():
             inst = institutions.first()
             print(f"   -> [CORRIGIENDO] Asignando todo a {inst.name}...")
             students.update(institution=inst)
             teachers.update(institution=inst)
             courses.update(institution=inst)
             print("   -> [OK] Datos académicos re-vinculados.")
    else:
        print("   -> Todos los registros académicos tienen institución asignada.")

if __name__ == '__main__':
    debug_data()
