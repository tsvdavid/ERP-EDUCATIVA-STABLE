
import os
import django
import sys
from datetime import date

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from users.models import User, Institution
from academic.models import AcademicYear, AcademicPeriod, Course, Subject, Enrollment, Grade, EvaluationCategory
from rest_framework.test import APIRequestFactory

def run_test():
    print(">>> INICIANDO PRUEBA FUNCIONAL: CICLO ACADÉMICO <<<\n")
    
    # Use atomic transaction to roll back changes at the end (keep DB clean)
    # OR keep them if we want to see data. For a "Test", usually we rollback or use test DB.
    # Since this is a "Functional Test" script requested by user to run on their dev env, 
    # I will create specific "TEST" data and NOT rollback automatically, but I'll make it distinguishable.
    # Actually, to avoid clutter, I'll delete created objects at the end explicitly or just leave them labeled TEST.
    # Let's use a unique prefix.
    PREFIX = "TEST_AUTO_"
    
    try:
        # 1. SETUP INSTITUTION & USERS
        print("[1] Configurando Datos Base (Institución, Usuarios)...")
        institution, _ = Institution.objects.get_or_create(name=f"{PREFIX}INSTITUTION")
        
        # Admin
        admin, _ = User.objects.get_or_create(username=f"{PREFIX}ADMIN", defaults={
            'email': 'admin@test.com', 'role': 'ADMIN', 'institution': institution
        })
        admin.set_password('testpass')
        admin.save()
        
        # Teacher
        teacher, _ = User.objects.get_or_create(username=f"{PREFIX}TEACHER", defaults={
            'email': 'teacher@test.com', 'role': 'TEACHER', 'institution': institution,
            'first_name': 'Profe', 'last_name': 'Test'
        })
        
        # Student
        student, _ = User.objects.get_or_create(username=f"{PREFIX}STUDENT", defaults={
            'email': 'student@test.com', 'role': 'STUDENT', 'institution': institution,
            'first_name': 'Estudiante', 'last_name': 'Test'
        })
        print("    > Usuarios creados/verificados.")

        # 2. ACADEMIC YEAR 2025 (OLD YEAR)
        print("\n[2] Ciclo 1: Año Lectivo 2025 (Pasado)")
        year_2025, _ = AcademicYear.objects.get_or_create(
            institution=institution, year=2025, 
            defaults={'name': 'Año 2025', 'start_date': '2025-01-01', 'end_date': '2025-12-31', 'is_active': False, 'is_closed': False}
        )
        # Ensure it has periods
        p1_2025, _ = AcademicPeriod.objects.get_or_create(year=year_2025, number=1, defaults={'name': 'Trimestre 1', 'start_date': '2025-01-01', 'end_date': '2025-04-01'})
        
        # Course & Enrollment 2025
        course_2025, _ = Course.objects.get_or_create(
            institution=institution, name=f"{PREFIX}Math 2025", 
            defaults={'year': 2025, 'level': '1', 'parallel': 'A'}
        )
        enrollment_2025, _ = Enrollment.objects.get_or_create(student=student, course=course_2025, defaults={'status': 'APPROVED'})
        subject_2025, _ = Subject.objects.get_or_create(course=course_2025, name="Matematicas", defaults={'teacher': teacher})
        
        print(f"    > Curso 2025 creado. Estudiante matriculado.")

        # 3. TEST PERIOD CLOSING LOGIC (IN 2025)
        print("\n[3] Prueba de Cierre de Periodos (Lógica de Bloqueo)")
        
        # Create a Grade Category
        cat_exam, _ = EvaluationCategory.objects.get_or_create(subject=subject_2025, name="Examen", defaults={'weight': 100, 'trimester': 1})
        
        # Create a Grade
        grade, created = Grade.objects.get_or_create(
            enrollment=enrollment_2025, subject=subject_2025, category=cat_exam,
            defaults={'score': 8.0}
        )
        print(f"    > Nota inicial creada: {grade.score}")
        
        # FORCE CLOSE PERIOD
        print("    > Cerrando Trimestre 1...")
        p1_2025.is_closed = True
        p1_2025.save()
        
        # Attempt to modify grade via ViewSet Logic (simulating API)
        # We need to instantiate the ViewSet and check validation manually or use the serializer validation logic
        from academic.serializers import GradeSerializer
        
        print("    > Intentando modificar nota en periodo cerrado...")
        data = {'score': 9.0, 'enrollment': enrollment_2025.id, 'subject': subject_2025.id, 'category': cat_exam.id}
        serializer = GradeSerializer(grade, data=data, partial=True)
        
        try:
            # Depending on how logic is implemented, it might be in perform_update or validate. 
            # In previous steps we added `_validate_year_period_open` in ViewSet calling it explicitly.
            # So Serializer alone might pass. We need to check the ViewSet method.
            from academic.views import GradeViewSet
            view = GradeViewSet()
            view.action = 'update'
            view.kwargs = {'pk': grade.id}
            
            # Mocking request isn't strictly necessary if we call the validator directly, 
            # but let's call the validator method we added.
            # However, we need to bypass 'self.get_object' in the method if we want to test easily, 
            # or mock it.
            # Let's construct a 'validated_data' dict that mimic what serializer returns
            validated_data_mock = {
                'enrollment': enrollment_2025,
                'category': cat_exam
            }
            
            # We need to handle the fact that the method looks for instance in self.get_object() if action is update
            # Let's temporarily monkeypatch get_object or just rely on the logic we saw:
            # "enrollment = validated_data.get('enrollment') or (instance.enrollment if instance else None)"
            # If we pass enrollment in validated_data, it uses it.
            
            try:
                view._validate_year_period_open(validated_data_mock)
                print("    [FALLO] El sistema PERMITIÓ modificación en periodo cerrado (Error).")
            except Exception as e:
                print(f"    [ÉXITO] El sistema BLOQUEÓ la modificación: {e}")
                
        except Exception as e:
             print(f"    [ERROR] Excepción inesperada: {e}")

        # RE-OPEN
        print("    > Re-abriendo Trimestre 1...")
        p1_2025.is_closed = False
        p1_2025.save()
        
        try:
            view._validate_year_period_open(validated_data_mock)
            print("    [ÉXITO] El sistema PERMITIÓ modificación tras re-apertura.")
        except Exception as e:
            print(f"    [FALLO] El sistema BLOQUEÓ tras re-apertura: {e}")


        # 4. NEW ACADEMIC YEAR (2026) - CLEAN SLATE
        print("\n[4] Ciclo 2: Nuevo Año Lectivo 2026 (Activo)")
        year_2026, _ = AcademicYear.objects.get_or_create(
            institution=institution, year=2026, 
            defaults={'name': 'Año 2026', 'start_date': '2026-01-01', 'end_date': '2026-12-31', 'is_active': True}
        )
        
        # Set 2025 Inactive
        year_2025.is_active = False
        year_2025.save()
        
        print("    > Año 2026 activado. Año 2025 desactivado.")
        
        # Test Filtering Logic (Simulated)
        # If we query Course.objects.all() via the ViewSet logic we added, we should only see 2026 stuff (which is empty so far).
        
        # Create 2026 Course
        course_2026, _ = Course.objects.get_or_create(
            institution=institution, name=f"{PREFIX}Math 2026", 
            defaults={'year': 2026, 'level': '1', 'parallel': 'A'}
        )
        
        # Simulate ViewSet Filtering
        # Logic: if no ?year= param, filter by active year (2026).
        print("    > Verificando filtros 'Clean Slate'...")
        
        # Mock Request 
        class MockRequest:
            def __init__(self, user, query_params):
                self.user = user
                self.query_params = query_params
                self.headers = {}

        from academic.views import CourseViewSet
        view_course = CourseViewSet()
        view_course.request = MockRequest(admin, {}) # No params
        
        qs = view_course.get_queryset()
        count_default = qs.count()
        
        # We expect to see ONLY the 2026 course (1), not 2025.
        # Wait, get_queryset starts with .all(). 
        # Check if our logic works.
        
        contains_2026 = qs.filter(id=course_2026.id).exists()
        contains_2025 = qs.filter(id=course_2025.id).exists()
        
        if contains_2026 and not contains_2025:
             print("    [ÉXITO] Filtro por defecto muestra SOLO Año Activo (2026).")
        else:
             print(f"    [FALLO] Filtro por defecto incorrecto. Contiene 2026? {contains_2026}. Contiene 2025? {contains_2025}.")
             
        # Test Explicit History Access
        view_course.request = MockRequest(admin, {'year': '2025'})
        qs_history = view_course.get_queryset()
        
        if qs_history.filter(id=course_2025.id).exists():
             print("    [ÉXITO] Filtro explícito (?year=2025) muestra datos históricos.")
        else:
             print("    [FALLO] No se pudo acceder al historial.")

        # 5. NEW ENROLLMENT (Matriculacion)
        print("\n[5] Nueva Matriculación en Año 2026")
        
        # Enroll student in 2026
        enrollment_2026, created = Enrollment.objects.get_or_create(
            student=student, course=course_2026, 
            defaults={'status': 'ENROLLED'}
        )
        
        if created:
            print("    [ÉXITO] Estudiante matriculado en 2026 correctamente.")
        else:
            print("    > Matricula 2026 ya existía.")
            
        print("\n>>> PRUEBA FUNCIONAL COMPLETADA <<<")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_test()
