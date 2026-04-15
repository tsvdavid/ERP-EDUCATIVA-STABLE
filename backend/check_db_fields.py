import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from learning.models import CourseCategory, CourseSubcategory
from academic.models import EvaluationCategory
from users.models import User

print("--- DIAGNÓSTICO DE CAMPOS ---")

def check_fields(model):
    print(f"\nModelo: {model.__name__}")
    fields = [f.name for f in model._meta.get_fields()]
    print(f"Campos detectados por Django: {fields}")

check_fields(User)
check_fields(EvaluationCategory)
check_fields(CourseCategory)
check_fields(CourseSubcategory)

print("\n--- FIN DEL DIAGNÓSTICO ---")
