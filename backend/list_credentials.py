import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Institution, User

def list_credentials():
    print("=== CREDENCIALES GENERADAS (PRISCA) ===")
    print("Contraseña para todos: admin123\n")
    
    try:
        inst = Institution.objects.get(name="Unidad Educativa Prisca")
    except:
        print("Institución Prisca no encontrada.")
        return

    # Rector
    rector = User.objects.filter(institution=inst, role='ADMIN').first()
    if rector:
        print(f"RECTOR:   {rector.username}  ({rector.first_name} {rector.last_name})")
    
    # Teachers
    print("\nPROFESORES (Ejemplos):")
    teachers = User.objects.filter(institution=inst, role='TEACHER')[:5]
    for t in teachers:
        print(f" - {t.username}  ({t.first_name} {t.last_name})")

    # Students
    print("\nESTUDIANTES (Ejemplos):")
    students = User.objects.filter(institution=inst, role='STUDENT')[:5]
    for s in students:
        course = s.enrollments.first().course.name if s.enrollments.exists() else "Sin curso"
        print(f" - {s.username}  ({s.first_name} {s.last_name}) -> {course}")

if __name__ == '__main__':
    list_credentials()
