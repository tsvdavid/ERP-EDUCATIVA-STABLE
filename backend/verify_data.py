import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from procedures.models import ProcedureTemplate

with open('verify_data_output.log', 'w') as f:
    f.write(f"Users in DB: {User.objects.count()}\n")
    f.write(f"Templates in DB: {ProcedureTemplate.objects.count()}\n")

print("Done")
