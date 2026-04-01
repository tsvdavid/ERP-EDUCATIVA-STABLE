import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from academic.models import AcademicYear, Course, EvaluationCategory, Grade
from accounting.models import FiscalYear
from communication.models import Notice, Holiday

print("--- ACADEMIC YEARS ---")
for ay in AcademicYear.objects.all().order_by('year'):
    print(f"ID: {ay.id}, Year: {ay.year}, Name: {ay.name}, Active: {ay.is_active}, Closed: {ay.is_closed}")
    courses = Course.objects.filter(year=ay.year).count()
    print(f"  Courses: {courses}")

print("\n--- FISCAL YEARS ---")
for fy in FiscalYear.objects.all().order_by('year'):
    print(f"ID: {fy.id}, Year: {fy.year}, Closed: {fy.is_closed}")

print("\n--- COMMUNICATION ---")
print(f"Total Notices: {Notice.objects.count()}")
print(f"Total Holidays: {Holiday.objects.count()}")
