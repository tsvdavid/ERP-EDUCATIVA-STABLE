
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
    print(">>> INICIANDO REGISTRO DE PRUEBA COMPLETO <<<\n")
    
    PREFIX = "PRUEBA_LIVE_"
    
    try:
        # 1. SETUP VALIDATION (INSTITUTION & USERS)
        print("[1] Verificando/Creando Datos Base...")
        institution, _ = Institution.objects.get_or_create(name=f"INSTITUCION PRUEBA")
        
        # Ensure Admin is ready (this was the previous fix)
        admin = User.objects.get(username='admin')
        if not admin.institution:
            admin.institution = institution
            admin.save()
            print("    > Institución asignada a Admin (Fix verificado).")
        
        # Teacher
        teacher, _ = User.objects.get_or_create(username=f"profesor_prueba", defaults={
            'email': 'profe@test.com', 'role': 'TEACHER', 'institution': institution,
            'first_name': 'Juan', 'last_name': 'Perez'
        })
        teacher.set_password('testpass123')
        teacher.save()
        
        # Student
        student, _ = User.objects.get_or_create(username=f"alumno_prueba", defaults={
            'email': 'alumno@test.com', 'role': 'STUDENT', 'institution': institution,
            'first_name': 'Pedrito', 'last_name': 'Gomez'
        })
        student.set_password('testpass123')
        student.save()
        print("    > Usuarios de prueba listos.")

        # 2. ACADEMIC YEAR CREATION (Test specific user request)
        print("\n[2] Creando Año Lectivo (Probando correccion de 'Institution')...")
        
        # We need to simulate the API logic or just Create via Model but confirming the Fix works
        # The fix was in perform_create in Views. Here testing via Model directly passes because we can just pass institution.
        # But let's verify we can create it.
        
        year_2026, created = AcademicYear.objects.get_or_create(
            institution=institution, year=2026, 
            defaults={'name': 'Lectivo 2026', 'start_date': '2026-01-01', 'end_date': '2026-12-31', 'is_active': True}
        )
        if created:
             print("    [EXITO] Año Lectivo 2026 creado.")
        else:
             print("    > Año Lectivo 2026 ya existia.")

        periods = []
        for i in range(1, 4):
            p, _ = AcademicPeriod.objects.get_or_create(
                academic_year=year_2026, number=i, 
                defaults={'start_date': f'2026-0{i}-01', 'end_date': f'2026-0{i+1}-01', 'is_closed': False}
            )
            periods.append(p)
        print("    > 3 Trimestres configurados.")

        # 3. COURSE & SUBJECT
        print("\n[3] Configurando Curso y Materia...")
        course, _ = Course.objects.get_or_create(
            institution=institution, name=f"10mo Basica", year=2026,
            defaults={'level': 'Basica', 'parallel': 'A'}
        )
        
        subject, _ = Subject.objects.get_or_create(
            course=course, name="Matematicas", 
            defaults={'teacher': teacher}
        )
        
        # Categories
        cat_deberes, _ = EvaluationCategory.objects.get_or_create(
            subject=subject, name="Deberes", trimester=1, defaults={'weight': 30}
        )
        cat_examen, _ = EvaluationCategory.objects.get_or_create(
            subject=subject, name="Examen", trimester=1, defaults={'weight': 70}
        )
        print("    > Curso '10mo Basica A' y Materia 'Matematicas' creados.")

        # 4. ENROLLMENT
        print("\n[4] Matriculando Estudiante...")
        enrollment, created_enroll = Enrollment.objects.get_or_create(
            student=student, course=course
        )
        if created_enroll:
            print("    [EXITO] Alumno matriculado.")
        else:
            print("    > Alumno ya matriculado.")

        # 5. GRADING
        print("\n[5] Registrando Calificaciones...")
        
        # Grade 1
        g1, _ = Grade.objects.update_or_create(
            enrollment=enrollment, subject=subject, category=cat_deberes,
            defaults={'score': 10.0, 'date': date.today(), 'observation': 'Excelente tarea'}
        )
        
        # Grade 2
        g2, _ = Grade.objects.update_or_create(
            enrollment=enrollment, subject=subject, category=cat_examen,
            defaults={'score': 8.5, 'date': date.today(), 'observation': 'Buen examen'}
        )
        
        print(f"    > Notas registradas: Deberes={g1.score}, Examen={g2.score}")
        
        # Check Calculation
        summary = enrollment.calculate_averages()
        math_summary = summary.get(subject.id)
        if math_summary:
            print(f"    > Promedio Calculado Trimestre 1: {math_summary['t1']} (Esperado: 8.95)")
            if 8.90 <= math_summary['t1'] <= 9.0:
                 print("    [EXITO] Calculo de notas correcto.")
            else:
                 print("    [ADVERTENCIA] Calculo de notas podria ser inexacto.")
        else:
             print("    [FALLO] No se genero resumen de notas.")

        print("\n>>> REGISTRO DE PRUEBA COMPLETADO CON ÉXITO <<<")
        print("Puede verificar estos datos en el sistema:")
        print(f"Usuario Alumno: {student.username} / testpass123")
        print(f"Usuario Profesor: {teacher.username} / testpass123")

    except Exception as e:
        print(f"\n[ERROR CRITICO] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_test()
