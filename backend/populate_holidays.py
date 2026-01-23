import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from communication.models import Holiday
import holidays
from datetime import date

# Populate 2025 and 2026
for year in [2025, 2026]:
    ec_holidays = holidays.EC(years=year)
    print(f"Populating Ecuador holidays for {year}...")
    for date_obj, name in ec_holidays.items():
        h, created = Holiday.objects.get_or_create(
            date=date_obj, 
            defaults={'name': name, 'is_system': True, 'description': 'Feriado Nacional'}
        )
        if created:
            print(f"Created: {date_obj} - {name}")
        else:
            print(f"Exists: {date_obj} - {name}")

print("Done.")
