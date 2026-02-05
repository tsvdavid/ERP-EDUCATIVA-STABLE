
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from communication.models import Notice

def check_users():
    print("--- Users Check ---")
    admins = User.objects.filter(role='ADMIN')
    for admin in admins:
        print(f"Admin: {admin.username}, Institution: {admin.institution}")

    rectors = User.objects.filter(role='RECTOR')
    for rector in rectors:
        print(f"Rector: {rector.username}, Institution: {rector.institution}")

    students = User.objects.filter(role='STUDENT')[:5]
    for student in students:
        print(f"Student: {student.username}, Institution: {student.institution}")

def check_notices():
    print("\n--- Notices Check ---")
    notices = Notice.objects.all().order_by('-created_at')[:5]
    for notice in notices:
        print(f"Notice: {notice.title}, Author: {notice.author.username}, Author Inst: {notice.author.institution}, Target: {notice.target_role}")

if __name__ == '__main__':
    check_users()
    check_notices()
