import os
import django
import sys
import random
import datetime
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    from faker import Faker
except ImportError:
    print("Error: 'faker' library not found. Please run 'pip install faker'")
    sys.exit(1)

from users.models import Institution, User
from academic.models import AcademicYear, AcademicPeriod, Course, Subject, EvaluationCategory, Enrollment, Grade, Attendance
from communication.models import Message, Notice

fake = Faker('es_ES')

def create_user(institution, role, first_name=None, last_name=None, extra_data={}):
    if not first_name:
        first_name = fake.first_name()
    if not last_name:
        last_name = fake.last_name()
    
    # Generate Username: First letter + Surname + optional number
    base_username = (first_name[0] + last_name).lower().replace(' ', '').replace('ñ', 'n')
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    user = User(
        username=username,
        email=f"{username}@prisca.edu.ec",
        first_name=first_name,
        last_name=last_name,
        role=role,
        institution=institution,
        password=make_password('admin123'), # Default password
        **extra_data
    )
    user.save()
    return user

def populate_prisca():
    print("=== POPULATING PRISCA DATA ===")
    
    INST_NAME = "Unidad Educativa Prisca"
    try:
        inst = Institution.objects.get(name=INST_NAME)
    except Institution.DoesNotExist:
        print(f"Creating Institution {INST_NAME}...")
        inst = Institution.objects.create(name=INST_NAME)

    with transaction.atomic():
        # 1. Academic Year
        print("1. Setting up Academic Year...")
        year_name = "2024-2025"
        ay, created = AcademicYear.objects.get_or_create(
            institution=inst,
            year=2024,
            defaults={
                'name': year_name,
                'start_date': datetime.date(2024, 9, 1),
                'end_date': datetime.date(2025, 6, 30),
                'is_active': True
            }
        )
        # Ensure periods exist
        t1, _ = AcademicPeriod.objects.get_or_create(academic_year=ay, number=1, defaults={'start_date': datetime.date(2024, 9, 1), 'end_date': datetime.date(2024, 11, 30), 'is_closed': True})
        t2, _ = AcademicPeriod.objects.get_or_create(academic_year=ay, number=2, defaults={'start_date': datetime.date(2024, 12, 1), 'end_date': datetime.date(2025, 3, 15), 'is_closed': False}) # ACTIVE
        t3, _ = AcademicPeriod.objects.get_or_create(academic_year=ay, number=3, defaults={'start_date': datetime.date(2025, 3, 16), 'end_date': datetime.date(2025, 6, 30), 'is_closed': False})

        # 2. Rector
        print("2. Creating Rector...")
        # Check if exists or create random
        if not User.objects.filter(institution=inst, role='ADMIN').exists():
            create_user(inst, 'ADMIN', first_name='Rector', last_name='Prisca')

        # 3. Teachers
        print("3. Creating Teachers...")
        grade_teachers = []
        for i in range(6): # One for each grade
            t = create_user(inst, 'TEACHER', extra_data={'address': fake.address(), 'phone': fake.phone_number()})
            grade_teachers.append(t)
        
        music_teacher = create_user(inst, 'TEACHER', first_name="Juan", last_name="Musica")
        pe_teacher = create_user(inst, 'TEACHER', first_name="Pedro", last_name="Deportes")

        # 4. Courses & Subjects
        print("4. Creating Courses (1-6) and Subjects...")
        courses = []
        for i in range(1, 7):
            c_name = f"{i}ro EGB"
            course, _ = Course.objects.get_or_create(
                institution=inst,
                name=c_name,
                year=2024,
                defaults={'level': 'Primaria', 'parallel': 'A'}
            )
            courses.append(course)

            # Subjects
            main_teacher = grade_teachers[i-1]
            subjects_data = [
                ('Matemáticas', main_teacher),
                ('Lengua y Literatura', main_teacher),
                ('Ciencias Naturales', main_teacher),
                ('Estudios Sociales', main_teacher),
                ('Música', music_teacher),
                ('Educación Física', pe_teacher)
            ]
            
            for subj_name, teacher in subjects_data:
                subj, _ = Subject.objects.get_or_create(
                    course=course,
                    name=subj_name,
                    defaults={'teacher': teacher}
                )
                
                # Evaluation Categories
                EvaluationCategory.objects.get_or_create(subject=subj, name='Lecciones', trimester=1, defaults={'weight': 30})
                EvaluationCategory.objects.get_or_create(subject=subj, name='Examen', trimester=1, defaults={'weight': 70})
                
                EvaluationCategory.objects.get_or_create(subject=subj, name='Lecciones', trimester=2, defaults={'weight': 30})
                EvaluationCategory.objects.get_or_create(subject=subj, name='Examen', trimester=2, defaults={'weight': 70})

        # 5. Students & Enrollments
        print("5. Creating Students and Enrollments...")
        for course in courses:
            print(f"   Populating {course.name}...")
            for s_idx in range(10): # 10 students
                student = create_user(inst, 'STUDENT', extra_data={'birth_date': fake.date_of_birth(minimum_age=6, maximum_age=12)})
                enrollment = Enrollment.objects.create(student=student, course=course)

                # Grades & Attendance
                subjects = course.subjects.all()
                for subj in subjects:
                    # T1 Grades (Closed - Full)
                    cats_t1 = subj.evaluation_categories.filter(trimester=1)
                    for cat in cats_t1:
                        # Random Low/High
                        score = round(random.uniform(5.0, 10.0), 2) if random.random() > 0.3 else round(random.uniform(2.0, 6.0), 2)
                        Grade.objects.create(
                            enrollment=enrollment,
                            subject=subj,
                            category=cat,
                            score=score,
                            date=t1.end_date - datetime.timedelta(days=random.randint(1, 20)),
                            observation=fake.sentence()
                        )
                    
                    # T2 Grades (Active - Partial)
                    cats_t2 = subj.evaluation_categories.filter(trimester=2)
                    for cat in cats_t2:
                        if random.choice([True, False]): # Not all graded yet
                            score = round(random.uniform(6.0, 10.0), 2)
                            Grade.objects.create(
                                enrollment=enrollment,
                                subject=subj,
                                category=cat,
                                score=score,
                                date=datetime.date.today(),
                                observation="Actividad reciente"
                            )

                # Attendance (Random last 30 days)
                for d in range(10):
                    date = datetime.date.today() - datetime.timedelta(days=d*2)
                    status = random.choices(['PRESENT', 'ABSENT', 'LATE'], weights=[80, 10, 10])[0]
                    Attendance.objects.create(
                        enrollment=enrollment,
                        date=date,
                        status=status,
                        remarks="Sin novedad" if status == 'PRESENT' else "Excusa pendiente"
                    )
        
        # 6. Communication
        print("6. Generating Communication...")
        rector = User.objects.filter(institution=inst, role='ADMIN').first()
        
        # Public Notice
        Notice.objects.create(
            author=rector,
            title="Suspensión de actividades por Feriado",
            content="Se informa a la comunidad que el día viernes no habrá asistencia.",
            target_role='ALL',
            event_date=datetime.date.today() + datetime.timedelta(days=3)
        )
        
        # Some messages
        random_teacher = grade_teachers[0]
        random_student = Enrollment.objects.first().student
        
        Message.objects.create(
            sender=random_teacher,
            recipient=random_student,
            subject="Recordatorio de Tarea",
            body="Por favor no olvides traer la maqueta mañana."
        )
        
        Message.objects.create(
            sender=random_student,
            recipient=random_teacher,
            subject="Pregunta sobre la maqueta",
            body="Profe, ¿puede ser de cartón?",
            parent=Message.objects.last()
        )

    print("=== POPULATION COMPLETE ===")

if __name__ == '__main__':
    populate_prisca()
