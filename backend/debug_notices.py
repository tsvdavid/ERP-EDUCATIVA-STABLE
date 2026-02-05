import os
import sys
import django
from django.db.models import Q

# Setup Django environment
sys.path.append(os.getcwd()) # Ensure current dir is in path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from communication.models import Notice
from users.models import User
from academic.models import Subject

def run_debug():
    print("--- Listing All Notices ---")
    notices = Notice.objects.all().order_by('-created_at')
    if not notices.exists():
        print("No notices found in database.")
    
    for n in notices:
        print(f"ID: {n.id} | Title: '{n.title}' | Role: {n.target_role} | Course: {n.target_course} | Students Count: {n.target_students.count()}")
        # Check if target_students is effectively null for different filter styles
        # n.target_students.all() exists?
        print(f"    - target_students.exists(): {n.target_students.exists()}")

    print("\n--- Testing Visibility for All Teachers ---")
    teachers = User.objects.filter(role='TEACHER')
    if not teachers.exists():
        print("No teachers found.")
        return

    # Pick first teacher
    teacher = teachers.first()
    print(f"Testing for Teacher: {teacher.username} (ID: {teacher.id})")
    
    # Get courses
    teacher_courses = Subject.objects.filter(teacher=teacher).values_list('course', flat=True)
    print(f"Teacher teaches in courses IDs: {list(teacher_courses)}")

    # Logic from Views.py (Current)
    queryset = Notice.objects.all()
    
    visible_qs = queryset.filter(
        Q(author=teacher) |
        (Q(target_course__isnull=True) & Q(target_students__isnull=True) & Q(target_role__in=['ALL', 'TEACHER'])) |
        (Q(target_course__in=teacher_courses) & Q(target_role__in=['ALL', 'TEACHER']))
    ).distinct()
    
    print(f"\nVisible Notices for {teacher.username}:")
    for n in visible_qs:
        print(f"  - [VISIBLE] ID: {n.id} | Title: {n.title}")

    # Identify MISSING notices that SHOULD be visible (Hypothetically)
    # i.e. Notices targeting TEACHER that are NOT in visible_qs
    print("\n--- Analysis of Hidden TEACHER Notices ---")
    hidden_teacher_notices = Notice.objects.filter(target_role='TEACHER').exclude(id__in=visible_qs.values_list('id', flat=True))
    
    if hidden_teacher_notices.exists():
        for n in hidden_teacher_notices:
            print(f"  - [HIDDEN] ID: {n.id} | Title: {n.title}")
            print(f"    Reason Analysis:")
            print(f"    - Target Role: {n.target_role}")
            print(f"    - Target Course: {n.target_course} (Teacher courses: {list(teacher_courses)})")
            print(f"    - Target Students Count: {n.target_students.count()} (Is Null Check would fail if count > 0?)")
            
            # Check clause 2: Global
            clause2 = (n.target_course is None) and (not n.target_students.exists()) and (n.target_role in ['ALL', 'TEACHER'])
            print(f"    - Global Clause Matches? {clause2}")
            if not clause2:
                print(f"       -> Course is None? {n.target_course is None}")
                print(f"       -> Students Empty? {not n.target_students.exists()}")
            
            # Check clause 3: Course
            clause3 = (n.target_course_id in teacher_courses) and (n.target_role in ['ALL', 'TEACHER'])
            print(f"    - Course Clause Matches? {clause3}")

    else:
        print("No notices targeting TEACHER are hidden. Everything seems correct?")

if __name__ == "__main__":
    run_debug()
