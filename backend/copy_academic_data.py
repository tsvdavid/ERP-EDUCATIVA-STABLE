import os
import django
import sys
from django.db import transaction

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Institution, User
from academic.models import AcademicYear, Course, Subject, EvaluationCategory, Enrollment, AcademicPeriod

def full_copy_academic(source_name, target_name):
    print(f"=== FULL MIGRATION: {source_name} -> {target_name} ===")

    try:
        source_inst = Institution.objects.get(name=source_name)
        target_inst = Institution.objects.get(name=target_name)
    except Institution.DoesNotExist as e:
        print(f"Error: Institution not found: {e}")
        return

    print(f"Source: {source_inst.name} (ID: {source_inst.id})")
    print(f"Target: {target_inst.name} (ID: {target_inst.id})")

    with transaction.atomic():
        # --- 1. CLEANUP ---
        print("\n1. CLEANUP: Deleting old data in Target...")
        
        # Delete Academic Structure
        del_years, _ = AcademicYear.objects.filter(institution=target_inst).delete()
        print(f"   Deleted {del_years} Academic Years (and cascades).")
        
        # Delete Users (Except Admin)
        target_users = User.objects.filter(institution=target_inst).exclude(username='admin').exclude(is_superuser=True)
        count = target_users.count()
        target_users.delete()
        print(f"   Deleted {count} Users (Students/Teachers) from Target.")
        
        # --- 2. COPY USERS ---
        print("\n2. COPY: Migrating Users...")
        user_map = {} # old_id -> new_instance
        source_users = User.objects.filter(institution=source_inst).exclude(username='admin').exclude(is_superuser=True)
        
        for user in source_users:
            # Handle username uniqueness
            # Clean username of previous suffixes if re-running or cross-copying
            base_username = user.username.split('_prisca')[0] 
            new_username = f"{base_username}_prisca" # Unique suffix
            
            # Check if exists (shouldn't if we just cleaned, but safety first)
            if User.objects.filter(username=new_username).exists():
                print(f"   [SKIP] User {new_username} already exists.")
                # Try to map it anyway
                user_map[user.id] = User.objects.get(username=new_username)
                continue

            new_user = User(
                username=new_username,
                email=user.email, # Emails can be duplicated usually
                first_name=user.first_name,
                last_name=user.last_name,
                second_name=user.second_name,
                second_surname=user.second_surname,
                cedula=user.cedula, # Unique constraint per institution!
                role=user.role,
                institution=target_inst,
                phone=user.phone,
                address=user.address,
                birth_date=user.birth_date,
                gender=user.gender,
                password=user.password # Copy Hash
            )
            # Handle CEDULA uniqueness
            # If cedula exists in target (maybe manually added admin?), skip or clear?
            # Model has Constraint: unique_cedula_per_institution
            # We already deleted users, so it should be fine.
            
            try:
                new_user.save()
                user_map[user.id] = new_user
            except Exception as e:
                print(f"   [ERROR] Failed to copy user {user.username}: {e}")

        print(f"   Copied {len(user_map)} users.")

        # --- 3. COPY ACADEMIC YEARS ---
        print("\n3. COPY: Academic Structure...")
        year_map = {}
        for ay in AcademicYear.objects.filter(institution=source_inst):
            new_ay = AcademicYear.objects.create(
                institution=target_inst,
                name=ay.name,
                year=ay.year,
                start_date=ay.start_date,
                end_date=ay.end_date,
                is_active=ay.is_active,
                is_closed=ay.is_closed
            )
            year_map[ay.id] = new_ay
            
            # Copy Periods
            for p in ay.periods.all():
                AcademicPeriod.objects.create(
                    academic_year=new_ay,
                    number=p.number,
                    start_date=p.start_date,
                    end_date=p.end_date,
                    is_closed=p.is_closed
                )

        # --- 4. COPY COURSES ---
        print("   Copying Courses...")
        course_map = {}
        for course in Course.objects.filter(institution=source_inst):
            new_course = Course.objects.create(
                institution=target_inst,
                name=course.name,
                level=course.level,
                parallel=course.parallel,
                year=course.year, # Assuming year matches, or we could look up mapped AcademicYear
                description=course.description
            )
            course_map[course.id] = new_course

        # --- 5. COPY SUBJECTS (With Teachers) ---
        print("   Copying Subjects...")
        for subj in Subject.objects.filter(course__institution=source_inst):
            # Find new course
            if subj.course.id not in course_map:
                continue
            
            new_course = course_map[subj.course.id]
            
            # Find new teacher
            new_teacher = None
            if subj.teacher and subj.teacher.id in user_map:
                new_teacher = user_map[subj.teacher.id]
            
            new_subj = Subject.objects.create(
                course=new_course,
                name=subj.name,
                teacher=new_teacher
            )
            
            # Copy Eval Categories
            for cat in subj.evaluation_categories.all():
                EvaluationCategory.objects.create(
                    subject=new_subj,
                    name=cat.name,
                    weight=cat.weight,
                    trimester=cat.trimester
                )

        # --- 6. COPY ENROLLMENTS ---
        print("\n4. COPY: Enrollments...")
        enroll_count = 0
        for enroll in Enrollment.objects.filter(course__institution=source_inst):
            if enroll.student.id in user_map and enroll.course.id in course_map:
                Enrollment.objects.create(
                    student=user_map[enroll.student.id],
                    course=course_map[enroll.course.id],
                    date_enrolled=enroll.date_enrolled
                )
                enroll_count += 1
        
        print(f"   Copied {enroll_count} enrollments.")

    print("\n=== MIGRATION COMPLETE ===")

if __name__ == '__main__':
    full_copy_academic("Unidad Educativa GitHub Copilot", "Unidad Educativa Prisca")
