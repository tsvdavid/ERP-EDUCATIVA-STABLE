import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User, Institution
from academic.models import AcademicYear, AcademicPeriod, Course, Subject, Enrollment, EvaluationCategory, Grade, Attendance, Observation
from communication.models import Message, Notice, Holiday
from django.db import transaction

class Command(BaseCommand):
    help = 'Populates the database with test data (Teachers, Students, Grades, etc.)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando población de datos...'))

        with transaction.atomic():
            # 1. Setup Institution
            institution, created = Institution.objects.get_or_create(
                name="Unidad Educativa GitHub Copilot",
                defaults={
                    'address': 'Calle Principal 123',
                    'email': 'info@copilot.edu.ec',
                    'phone': '0991234567'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Institución creada: {institution.name}'))
            else:
                self.stdout.write(f'Usando institución: {institution.name}')

            # 2. Setup Academic Year 2026
            year_name = "2026-2027"
            academic_year, created = AcademicYear.objects.get_or_create(
                institution=institution,
                year=2026,
                defaults={
                    'name': year_name,
                    'start_date': date(2026, 4, 1),
                    'end_date': date(2027, 2, 1),
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Año Lectivo creado: {academic_year.name}'))

            # Setup Periods (Trimesters)
            t1, _ = AcademicPeriod.objects.get_or_create(
                academic_year=academic_year, number=1,
                defaults={'start_date': date(2026, 4, 1), 'end_date': date(2026, 7, 15)}
            )
            t2, _ = AcademicPeriod.objects.get_or_create(
                academic_year=academic_year, number=2,
                defaults={'start_date': date(2026, 7, 16), 'end_date': date(2026, 11, 15)}
            )
            t3, _ = AcademicPeriod.objects.get_or_create(
                academic_year=academic_year, number=3,
                defaults={'start_date': date(2026, 11, 16), 'end_date': date(2027, 2, 1)}
            )
            self.stdout.write(f'Trimestres verificados.')

            # 3. Create Teachers
            # 5 Grade Teachers + 3 Specialists
            teachers_data = [
                ('Juan', 'Pérez', 'Primero EGB'),
                ('Maria', 'López', 'Segundo EGB'),
                ('Carlos', 'García', 'Tercero EGB'),
                ('Ana', 'Torres', 'Cuarto EGB'),
                ('Luis', 'Mendoza', 'Quinto EGB'),
                ('Jose', 'Valencia', 'Música'), 
                ('Sofia', 'Ramirez', 'Educación Física'),
                ('David', 'Castro', 'Informática'),
            ]

            from typing import List
            teachers: List[User] = []
            for first, last, specialization in teachers_data:
                username = f"{first[0].lower()}{last.lower()}"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first,
                        'last_name': last,
                        'email': f"{username}@copilot.edu.ec",
                        'role': User.Role.TEACHER,
                        'institution': institution,
                        'is_staff': False
                    }
                )
                if created:
                    user.set_password('admin123')
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Profesor creado: {first} {last} ({username})'))
                teachers.append(user)

            # Assign roles/specialties for easy access
            grade_teachers = teachers[:5]
            music_teacher = teachers[5]
            pe_teacher = teachers[6]
            info_teacher = teachers[7]

            # 4. Create Courses (1st to 5th)
            courses = []
            levels = [
                ("Primero EGB", "1"),
                ("Segundo EGB", "2"),
                ("Tercero EGB", "3"),
                ("Cuarto EGB", "4"),
                ("Quinto EGB", "5"),
            ]

            for i, (name, level_code) in enumerate(levels):
                course, created = Course.objects.get_or_create(
                    name=name,
                    institution=institution,
                    year=2026,
                    defaults={
                        'level': level_code,
                        'parallel': 'A',
                        'description': f'Aula de {name}'
                    }
                )
                if created:
                     self.stdout.write(self.style.SUCCESS(f'Curso creado: {course}'))
                courses.append(course)

                # Create Subjects for this course
                main_teacher = grade_teachers[i]
                
                # Main Subjects (assigned to grade teacher)
                main_subjects = ['Matemáticas', 'Lengua y Literatura', 'Ciencias Naturales', 'Estudios Sociales']
                for sub_name in main_subjects:
                    Subject.objects.get_or_create(
                        course=course, name=sub_name,
                        defaults={'teacher': main_teacher}
                    )

                # Special Subjects
                Subject.objects.get_or_create(course=course, name='Música', defaults={'teacher': music_teacher})
                Subject.objects.get_or_create(course=course, name='Educación Física', defaults={'teacher': pe_teacher})
                Subject.objects.get_or_create(course=course, name='Informática', defaults={'teacher': info_teacher})

            # 5. Create Students (4 per course = 20 total)
            student_names = [
                ("Andres", "Vera"), ("Beatriz", "Zambrano"), ("Camilo", "Díaz"), ("Diana", "Fuentes"),
                ("Eduardo", "Gómez"), ("Fernanda", "Hidalgo"), ("Gabriel", "Ibarra"), ("Helena", "Jaramillo"),
                ("Ivan", "Karam"), ("Julia", "Lara"), ("Kevin", "Montoya"), ("Laura", "Nuñez"),
                ("Manuel", "Ortega"), ("Natalia", "Paz"), ("Oscar", "Quezada"), ("Paula", "Rios"),
                ("Quintin", "Salas"), ("Rosa", "Torres"), ("Santiago", "Uribe"), ("Tania", "Vargas")
            ]

            all_students = []
            student_idx: int = 0
            
            for course in courses:
                # Assign 4 students per course
                for _ in range(4):
                    if student_idx >= len(student_names): break
                    first, last = student_names[student_idx]
                    username = f"{first[0].lower()}{last.lower()}"
                    
                    # Ensure unique username if duplicates exist (though basic logic here)
                    if User.objects.filter(username=username).exists():
                         username = f"{username}{random.randint(1,99)}"

                    student, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': first,
                            'last_name': last,
                            'email': f"{username}@student.copilot.edu.ec",
                            'role': User.Role.STUDENT,
                            'institution': institution
                        }
                    )
                    if created:
                        student.set_password('admin123')
                        student.save()
                        self.stdout.write(self.style.SUCCESS(f'Estudiante creado: {first} {last} ({username})'))
                    
                    # Enroll in course
                    enrollment, _ = Enrollment.objects.get_or_create(student=student, course=course)
                    all_students.append(enrollment)
                    student_idx += 1

            # 6. Generate Data (Grades, Attendance, etc.)
            
            # Categories for evaluation
            # For each subject, we need categories for each trimester
            # Structure: Parcial 1 (40%), Parcial 2 (40%), Examen (20%) for each Trimester
            # Or simplified: Aporte (70%), Examen (30%)
            
            self.stdout.write("Generando Calificaciones...")
            all_subjects = Subject.objects.all()
            for subject in all_subjects:
                # Create categories if not exist
                for trim in [1, 2, 3]:
                    EvaluationCategory.objects.get_or_create(
                        subject=subject, name=f'Aportes T{trim}', trimester=trim, defaults={'weight': 70.00}
                    )
                    EvaluationCategory.objects.get_or_create(
                        subject=subject, name=f'Examen T{trim}', trimester=trim, defaults={'weight': 30.00}
                    )

            # Fill Grades
            # T1 and T2: Complete
            # T3: Active (Partial)
            
            for enrollment in all_students: # Iterate all enrollments
                for subject in enrollment.course.subjects.all():
                    cats = subject.evaluation_categories.all()
                    
                    # Determine student "academic level" randomly (High, Medium, Low)
                    perf_type = random.choice(['high', 'medium', 'low', 'mixed'])
                    
                    for cat in cats:
                        # Skip T3 Examen (not yet taken)
                        if cat.trimester == 3 and 'Examen' in cat.name:
                            continue
                            
                        # Generate score based on perf
                        if perf_type == 'high':
                            score = random.uniform(8.5, 10.0)
                        elif perf_type == 'low':
                            score = random.uniform(4.0, 7.5)
                        else:
                            score = random.uniform(6.0, 9.0)
                            
                        # Create Grade
                        Grade.objects.get_or_create(
                            enrollment=enrollment,
                            subject=subject,
                            category=cat,
                            defaults={
                                'score': round(float(score), 2),
                                'date': date.today(),
                                'observation': 'Buen trabajo' if score > 8 else 'Mejorar'
                            }
                        )

            # 7. Attendance
            self.stdout.write("Generando Asistencia...")
            # Generate random absences for last 30 days
            start_date = date.today() - timedelta(days=30)
            for i in range(30):
                day = start_date + timedelta(days=i)
                if day.weekday() >= 5: continue # Skip weekend
                
                for enrollment in all_students:
                    # 5% chance of absence
                    if random.random() < 0.05:
                        Attendance.objects.create(
                            enrollment=enrollment,
                            date=day,
                            status=Attendance.Status.ABSENT,
                            remarks="Enfermedad" if random.choice([True, False]) else "Falta injustificada"
                        )
                    # Note: We assume missing record = present via Frontend logic usually, or we can create PRESENT records.
                    # Creating only ABSENT/LATE is cleaner for DB size in demos.

            # 8. Communication (Notices & Messages)
            self.stdout.write("Generando Comunicación...")
            
            # Global Notice
            rector, _ = User.objects.get_or_create(username='admin', defaults={'role': 'ADMIN'})
            Notice.objects.create(
                author=rector,
                title="Bienvenida al Año Lectivo 2026-2027",
                content="Estimada comunidad educativa, damos inicio a un nuevo año de aprendizaje...",
                target_role=Notice.TargetRole.ALL
            )
            
            # Teacher Notices (Avisos)
            for teacher in grade_teachers:
                # Notice for their course
                # Find a course they teach
                sub = Subject.objects.filter(teacher=teacher).first()
                if sub:
                    Notice.objects.create(
                        author=teacher,
                        title="Reunión de Padres de Familia",
                        content="Se convoca a reunión para discutir el avance del primer trimestre.",
                        target_role=Notice.TargetRole.PARENTS,
                        target_course=sub.course
                    )

            # Messages (Buzón) - Teacher replying to Student
            # Pick a random student
            random_enrollment = random.choice(all_students)
            student = random_enrollment.student
            teacher = random_enrollment.course.subjects.first().teacher
            
            msg = Message.objects.create(
                sender=student,
                recipient=teacher,
                subject="Pregunta sobre deber",
                body="Profe, no entiendo el ejercicio 3 de matemáticas.",
                is_read=True
            )
            
            # Reply
            Message.objects.create(
                sender=teacher,
                recipient=student,
                subject="Re: Pregunta sobre deber",
                body="Hola, revisa la página 45 del libro, ahí está la fórmula.",
                parent=msg,
                is_read=False
            )

            # 9. Holidays
            Holiday.objects.get_or_create(
                date=date(2026, 5, 24),
                name="Batalla de Pichincha"
            )
            Holiday.objects.get_or_create(
                date=date(2026, 11, 2),
                name="Día de los Difuntos"
            )
            # Fiestas Patronales (Requested)
            Holiday.objects.get_or_create(
                date=date(2026, 10, 15), # Example date
                name="Fiestas Patronales de la Institución",
                description="Celebración del aniversario de la institución con eventos culturales y deportivos."
            )

            self.stdout.write(self.style.SUCCESS('¡Datos de prueba poblados exitosamente!'))
