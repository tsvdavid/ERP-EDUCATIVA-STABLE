
import os
import django
import sys
from datetime import datetime

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, Institution
from communication.models import Notice
from rest_framework.test import APIRequestFactory, force_authenticate
from communication.views import NoticeViewSet

def verify_fix():
    print("--- Starting Verification ---")
    
    # 1. Create Institution
    inst, _ = Institution.objects.get_or_create(name="Test Institution Verification", defaults={'ruc': '1234567890001'})
    print(f"Institution: {inst.name}")

    # 2. Create Global Admin (No Institution)
    global_admin, created = User.objects.get_or_create(username="global_admin_verify", defaults={'role': 'ADMIN', 'email': 'global@admin.com'})
    global_admin.institution = None
    global_admin.save()
    print(f"Global Admin: {global_admin.username} (Inst: {global_admin.institution})")

    # 3. Create Student (With Institution)
    student, created = User.objects.get_or_create(username="student_verify", defaults={'role': 'STUDENT', 'email': 'student@verify.com'})
    student.institution = inst
    student.save()
    print(f"Student: {student.username} (Inst: {student.institution})")

    # 4. Create Global Notice
    notice = Notice.objects.create(
        title="Global Notice Verification",
        content="This is a test notice from global admin.",
        author=global_admin,
        target_role='ALL'
    )
    print(f"Created Notice: {notice.title} by {notice.author.username}")

    # 5. Check Visibility via ViewSet
    factory = APIRequestFactory()
    view = NoticeViewSet.as_view({'get': 'list'})

    request = factory.get('/api/communication/notices/')
    force_authenticate(request, user=student)
    
    response = view(request)
    
    found = False
    for n in response.data:
        if n['id'] == notice.id:
            found = True
            break
            
    if found:
        print("✅ SUCCESS: Student can see Global Notice!")
    else:
        print("❌ FAILURE: Student cannot see Global Notice.")

    # Cleanup (Optional)
    # notice.delete()
    # student.delete()
    # global_admin.delete()
    # inst.delete()

if __name__ == '__main__':
    verify_fix()
