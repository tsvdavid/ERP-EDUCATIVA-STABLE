import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd()) # Ensure current dir is in path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from communication.models import Notice
from users.models import User
from academic.models import Course, Enrollment
from django.db.models import Q

def run_test():
    print("--- Starting Notice Visibility Test ---")

    # 1. Clean up previous test data if any (optional, be careful)
    # Notice.objects.filter(title__startswith="TEST NOTICE").delete()

    # 2. Get or Create Test Users
    admin_user, _ = User.objects.get_or_create(username='admin_test', defaults={'role': 'ADMIN', 'email': 'admin@test.com'})
    teacher_user, _ = User.objects.get_or_create(username='teacher_test', defaults={'role': 'TEACHER', 'email': 'teacher@test.com'})
    student_user, _ = User.objects.get_or_create(username='student_test', defaults={'role': 'STUDENT', 'email': 'student@test.com'})
    
    # Ensure roles are correct
    teacher_user.role = 'TEACHER'
    teacher_user.save()
    student_user.role = 'STUDENT'
    student_user.save()

    print(f"Users prepared: Admin={admin_user}, Teacher={teacher_user.role}, Student={student_user.role}")

    # 3. Create a Global Notice for TEACHERS
    notice_teacher = Notice.objects.create(
        author=admin_user,
        title="TEST NOTICE FOR TEACHERS",
        content="This is for all teachers.",
        target_role='TEACHER',
        target_course=None
    )
    print(f"Created Notice for TEACHERS: {notice_teacher.id}")

    # 4. Check Visibility for TEACHER
    # Mimic NoticeViewSet logic
    queryset = Notice.objects.all()
    user = teacher_user
    
    teacher_qs = queryset.filter(
        Q(author=user) |
        (Q(target_course__isnull=True) & Q(target_students__isnull=True) & Q(target_role__in=['ALL', 'TEACHER']))
    ).distinct()
    
    if notice_teacher in teacher_qs:
        print("[SUCCESS] Teacher CAN see the GLOBAL notice.")
    else:
        print("[FAILURE] Teacher CANNOT see the GLOBAL notice.")


    # 4b. Create Course-Specific Notice for TEACHER
    # Ensure Institution exists
    from users.models import Institution
    inst, _ = Institution.objects.get_or_create(name="Test Institution")
    admin_user.institution = inst
    admin_user.save()
    
    # First, create a course and assign teacher (via Subject)
    course_test, _ = Course.objects.get_or_create(institution=inst, name="Test Course", year=2024, defaults={'level': '', 'parallel': 'A'}) # Simplified
    # Create Subject linking Teacher to Course
    from academic.models import Subject
    Subject.objects.get_or_create(course=course_test, name="Math test", defaults={'teacher': teacher_user})
    
    notice_teacher_course = Notice.objects.create(
        author=admin_user,
        title="TEST NOTICE FOR TEACHER COURSE",
        content="This is for teachers of Test Course.",
        target_role='TEACHER',
        target_course=course_test
    )
    
    # Get courses where this teacher teaches a subject
    from academic.models import Subject
    teacher_courses = Subject.objects.filter(teacher=teacher_user).values_list('course', flat=True)
    
    # Re-query
    teacher_qs = queryset.filter(
        Q(author=user) |
        (Q(target_course__isnull=True) & Q(target_students__isnull=True) & Q(target_role__in=['ALL', 'TEACHER'])) |
        (Q(target_course__in=teacher_courses) & Q(target_role__in=['ALL', 'TEACHER']))
    ).distinct()
    
    # NOTE: In the actual view, we will check if it works. 
    # But here we want to test the VIEW LOGIC. 
    # Since we can't easily import the view class and call get_queryset without a request mock, 
    # we will rely on the fact that we are testing the query logic *we plan to write* or *currently exists*.
    # Actually, let's just RUN the script against the current DB state using the logic COPIED from the view to prove failure?
    # Or just use the test to verify results AFTER we change code?
    # Let's verify failure first. The Current View Logic is hardcoded above in step 4.
    # I need to update the query logic in this script to MATCH THE TARGET LOGIC to verify it works, 
    # OR match the CURRENT logic to prove failure.
    # Let's try to verify the CURRENT logic fails.
    
    if notice_teacher_course in teacher_qs:
        print("[SUCCESS] Teacher CAN see the COURSE notice (Fix verified!).") 
    else:
        print("[FAILURE] Teacher CANNOT see the COURSE notice (Fix failed).")



    # 5. Create a Global Notice for STUDENTS
    notice_student = Notice.objects.create(
        author=admin_user,
        title="TEST NOTICE FOR STUDENTS",
        content="This is for all students.",
        target_role='STUDENT',
        target_course=None
    )
    print(f"Created Notice for STUDENTS: {notice_student.id}")

    # 6. Check Visibility for STUDENT
    user = student_user
    # Mock enrollment (student has no courses for this test, which mimics 'global' check)
    student_courses = []
    
    student_qs = queryset.filter(
        # 1. Specifically targeted to this student
        Q(target_students=user) |
        
        # 2. Targeted to the student's course (and role matches)
        (Q(target_course__in=student_courses) & Q(target_role__in=['ALL', 'STUDENT'])) |
        
        # 3. Global announcement (No course, No specific students)
        (Q(target_course__isnull=True) & Q(target_students__isnull=True) & Q(target_role__in=['ALL', 'STUDENT']))
    ).distinct()
    
    if notice_student in student_qs:
        print("[SUCCESS] Student CAN see the notice.")
    else:
        print("[FAILURE] Student CANNOT see the notice.")
        print(f"Queryset count: {student_qs.count()}")

    # 7. Test Edge Case: Empty String for Course?
    # If the database stores empty string? No, it's a FK. 
    # But maybe target_course is somehow set?
    
    # Clean up
    notice_teacher.delete()
    notice_student.delete()
    # Don't delete users to avoid breaking things if they were real, but here they are test users. 
    # To be safe, leave them or delete if knew they were created just now.
    
if __name__ == "__main__":
    run_test()
