import os
import django
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from academic.models import Course, Subject, ClassSchedule

def run():
    print("Borrando horarios anteriores para empezar desde cero...")
    ClassSchedule.objects.all().delete()

    TIME_SLOTS = [
        (time(8, 0), time(8, 45)),
        (time(8, 45), time(9, 30)),
        (time(9, 45), time(10, 30)),
        (time(10, 30), time(11, 15)),
        (time(11, 15), time(12, 0)),
        (time(12, 0), time(12, 45)),
    ]

    courses = Course.objects.all()
    count = 0

    for course in courses:
        subjects = Subject.objects.filter(course=course)
        
        day = 1
        slot_idx = 0
        
        for subject in subjects:
            # Asignar 2 bloques por materia
            for _ in range(2):
                start_time, end_time = TIME_SLOTS[slot_idx]
                
                ClassSchedule.objects.create(
                    subject=subject,
                    day_of_week=day,
                    start_time=start_time,
                    end_time=end_time
                )
                count += 1
                
                slot_idx += 1
                if slot_idx >= len(TIME_SLOTS):
                    slot_idx = 0
                    day += 1
                    if day > 5:
                        day = 1

    print(f"¡Listo! Se generaron {count} bloques de horario en total para todos los cursos.")

if __name__ == '__main__':
    run()
