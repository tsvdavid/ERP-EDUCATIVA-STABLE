import os
import django
from datetime import date
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, Institution
from academic.models import AcademicYear, AcademicPeriod, Course, Subject, Enrollment, Grade, Attendance, EvaluationCategory
from rest_framework.test import APIRequestFactory, force_authenticate
from academic.views import GradeViewSet, AttendanceViewSet

def run_verification():
    print("--- Starting Verification ---")
    
    # 1. Setup Data
    institution, _ = Institution.objects.get_or_create(name="Test Inst")
    
    # User
    teacher, _ = User.objects.get_or_create(username="teacher_verif", defaults={'email':"t@test.com", 'role':"TEACHER", 'institution':institution})
    if teacher.role != 'TEACHER':
        teacher.role = 'TEACHER'
        teacher.institution = institution
        teacher.save()
        
    student, _ = User.objects.get_or_create(username="student_verif", defaults={'email':"s@test.com", 'role':"STUDENT", 'institution':institution})
    if student.role != 'STUDENT':
        student.role = 'STUDENT'
        student.institution = institution
        student.save()
    
    # 2. Academic Year
    year_val = 2026
    acad_year, created = AcademicYear.objects.get_or_create(
        institution=institution, 
        year=year_val,
        defaults={
            'name': '2026',
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
            'is_active': True,
            'is_closed': False
        }
    )
    # Force open
    acad_year.is_closed = False
    acad_year.save()
        
    # Periods
    p1, _ = AcademicPeriod.objects.get_or_create(
        academic_year=acad_year, 
        number=1, 
        defaults={
            'start_date': date(2026,1,1), 
            'end_date': date(2026,3,30),
            'is_closed': False
        }
    )
    # Force open
    p1.is_closed = False
    p1.save()
    
    # Course & Subject
    course, _ = Course.objects.get_or_create(institution=institution, name="Math 101", year=year_val, defaults={'level': '1', 'parallel': 'A'})
    subject, _ = Subject.objects.get_or_create(course=course, name="Algebra", defaults={'teacher':teacher})
    if subject.teacher != teacher:
        subject.teacher = teacher
        subject.save()
    
    # Category (Trimestre 1)
    cat1, _ = EvaluationCategory.objects.get_or_create(subject=subject, name="Exam 1", trimester=1, defaults={'weight': 100})
    
    # Enrollment
    enrollment, _ = Enrollment.objects.get_or_create(student=student, course=course)
    
    # 3. Test Grading (Open)
    print("\n[TEST] Grading when PERIOD OPEN")
    factory = APIRequestFactory()
    view = GradeViewSet.as_view({'post': 'create'})
    
    # Clean up existing grade for this category to ensure create works or use update if exists
    existing_grade = Grade.objects.filter(enrollment=enrollment, category=cat1).first()
    if existing_grade:
        existing_grade.delete()

    data = {
        'enrollment': enrollment.id,
        'subject': subject.id,
        'category': cat1.id,
        'score': 10.0,
        'date': '2026-01-15'
    }
    
    request = factory.post('/api/academic/grades/', data, format='json')
    force_authenticate(request, user=teacher)
    response = view(request)
    
    grade_id = None
    if response.status_code == 201:
        print("PASS: Grade created successfully.")
        grade_id = response.data['id']
    else:
        print(f"FAIL: Grade creation failed: {response.data}")
        # Try to find if it was created despite error or previous one?
        return

    # 4. Test Grading (Closed)
    print("\n[TEST] Grading when PERIOD CLOSED")
    p1.is_closed = True
    p1.save()
    
    # Try updating
    view_update = GradeViewSet.as_view({'patch': 'partial_update'})
    data_update = {'score': 5.0}
    request = factory.patch(f'/api/academic/grades/{grade_id}/', data_update, format='json')
    force_authenticate(request, user=teacher)
    try:
        response = view_update(request, pk=grade_id)
        # Note: Depending on implementation, it might validation error (400) or permission denied (403)
        if response.status_code == 400 and "cerrado" in str(response.data):
             print(f"PASS: Blocked correctly: {response.data}")
        else:
             print(f"FAIL: Should have blocked! Status: {response.status_code}, Data: {response.data}")
    except Exception as e:
        print(f"FAIL: Exception raised: {e}")
        import traceback
        traceback.print_exc()

    # Re-open for cleanup/safety
    p1.is_closed = False
    p1.save()
    
    # 5. Test Attendance Report
    print("\n[TEST] Attendance Report")
    Attendance.objects.update_or_create(enrollment=enrollment, date='2026-01-01', defaults={'status': 'PRESENT'})
    Attendance.objects.update_or_create(enrollment=enrollment, date='2026-01-02', defaults={'status': 'ABSENT'})
    
    view_report = AttendanceViewSet.as_view({'get': 'report'})
    request = factory.get(f'/api/academic/attendance/report/?course_id={course.id}')
    force_authenticate(request, user=teacher)
    response = view_report(request)
    
    if response.status_code == 200:
        print(f"PASS: Report generated. Data: {response.data}")
        # Find our student in the list
        entry = next((item for item in response.data if item['student_id'] == student.id), None)
        if entry:
             if entry['present'] == 1 and entry['absent'] == 1:
                 print("PASS: Data accuracy verified.")
             else:
                 print(f"FAIL: Data counts mismatch. Got {entry}")
        else:
             print("FAIL: Student not found in report.")
    else:
        print(f"FAIL: {response.status_code} {response.data}")

if __name__ == "__main__":
    run_verification()
