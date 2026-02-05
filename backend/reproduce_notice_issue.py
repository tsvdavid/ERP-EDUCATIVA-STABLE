import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from communication.models import Notice
from rest_framework.test import APIRequestFactory, force_authenticate
from communication.views import NoticeViewSet

def run_test():
    # 1. Setup Data
    print("Setting up data...")
    # Create Admin
    admin, _ = User.objects.get_or_create(username='admin_test', defaults={'email': 'admin@test.com', 'role': 'ADMIN'})
    
    # Create Teacher
    teacher, _ = User.objects.get_or_create(username='teacher_test', defaults={'email': 'teacher@test.com', 'role': 'TEACHER'})
    
    # Create Student
    student, _ = User.objects.get_or_create(username='student_test', defaults={'email': 'student@test.com', 'role': 'STUDENT'})
    
    # Create Notice for Teachers with dates (simulate problem)
    # Start date = yesterday, End date = tomorrow (should be active)
    now = timezone.now()
    start_date = now - timedelta(days=1)
    end_date = now + timedelta(days=1)
    
    notice_teacher = Notice.objects.create(
        author=admin,
        title="Test Notice for Teachers",
        content="This is a test content.",
        target_role='TEACHER', # Targeted to teachers
        event_date=start_date,
        event_end_date=end_date
    )
    
    notice_student = Notice.objects.create(
        author=admin,
        title="Test Notice for Students",
        content="This is a test content.",
        target_role='STUDENT', # Targeted to students
        event_date=start_date,
        event_end_date=end_date
    )

    print(f"Created Notice {notice_teacher.id} for TEACHER: {notice_teacher.title}")
    print(f"Created Notice {notice_student.id} for STUDENT: {notice_student.title}")

    # 2. Test API as Teacher
    factory = APIRequestFactory()
    view = NoticeViewSet.as_view({'get': 'list'})

    print("\n--- Testing as TEACHER ---")
    request = factory.get('/api/communication/notices/')
    force_authenticate(request, user=teacher)
    response = view(request)
    
    found = False
    for n in response.data:
        # Note: API might be paginated? If ModelViewSet uses pagination. Default usually page size 100 or paginated.
        # Check if 'results' in response.data
        data_list = n if isinstance(n, dict) and 'id' in n else (response.data.get('results', []) if isinstance(response.data, dict) else response.data)
        
        # Adjust logic if result is list
        if isinstance(response.data, list):
             data_list = response.data
        elif 'results' in response.data:
             data_list = response.data['results']
        
    # Re-iterate correctly
    final_list = data_list if isinstance(data_list, list) else []
    ids = [x['id'] for x in final_list]
    print(f"Notices visible to Teacher: {ids}")
    
    if notice_teacher.id in ids:
        print("SUCCESS: Teacher sees the notice.")
    else:
        print("FAILURE: Teacher DOES NOT see the notice.")

    print("\n--- Testing as STUDENT ---")
    request = factory.get('/api/communication/notices/')
    force_authenticate(request, user=student)
    response = view(request)
    
    data_list_s = response.data.get('results', []) if isinstance(response.data, dict) else response.data
    ids_s = [x['id'] for x in data_list_s]
    print(f"Notices visible to Student: {ids_s}")

    if notice_student.id in ids_s:
        print("SUCCESS: Student sees the notice.")
    else:
        print("FAILURE: Student DOES NOT see the notice.")

    # Cleanup
    # notice_teacher.delete() 
    # notice_student.delete()
    # Users kept for debug

if __name__ == '__main__':
    try:
        run_test()
    except Exception as e:
        import traceback
        traceback.print_exc()
