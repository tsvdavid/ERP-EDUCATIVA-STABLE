import os
import sys
import django

sys.path.append('/var/www/erpeducativa/ERP-EDUCATIVA/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from procedures.models import ProcedureTemplate, StudentRequest

print("Procedure templates count:", ProcedureTemplate.objects.count())
print("Student requests count:", StudentRequest.objects.count())
print("Models successfully queried!")
