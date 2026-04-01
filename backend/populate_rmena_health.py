import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from health.models import MedicalRecord, MedicalVisit, DeceRecord, DeceVisit

def run():
    try:
        student = User.objects.get(username='rmena', role='STUDENT')
    except User.DoesNotExist:
        print("Student rmena not found.")
        return

    admin = User.objects.filter(role='ADMIN').first()
    if not admin:
        admin = User.objects.first() # Fallback

    # MEDICAL RECORD
    m_record, created = MedicalRecord.objects.get_or_create(student=student)
    m_record.blood_type = 'O+'
    m_record.allergies = 'Alergia a la penicilina y picaduras de abeja'
    m_record.chronic_conditions = 'Asma infantil (requiere inhalador)'
    m_record.regular_medication = 'Salbutamol solo en caso de ahogo o crisis'
    m_record.emergency_contact_name = 'Carmen Rojas'
    m_record.emergency_contact_phone = '0987654321'
    m_record.emergency_contact_relationship = 'Abuela Materna'
    m_record.save()

    # MEDICAL VISIT
    MedicalVisit.objects.create(
        student=student,
        doctor=admin,
        date=timezone.now() - timezone.timedelta(days=3),
        reason='Dolor de cabeza severo y mareos',
        symptoms='Temperatura 37.5, palidez, queja de dolor punzante en la sien',
        diagnosis='Cefalea por tensión',
        treatment='Reposo de 1 hora en enfermería, toma de Paracetamol 500mg, hidratación con suero',
        notes='El alumno se reincorporó normalmente a su clase posterior.'
    )

    # DECE RECORD
    d_record, created = DeceRecord.objects.get_or_create(student=student)
    d_record.family_context = 'Familia monoparental, actualmente vive con la madre y abuelos.'
    d_record.academic_background = 'Rendimiento estándar, aunque reporta una fuerte bajada en materias exactas este trimestre.'
    d_record.has_special_needs = True
    d_record.special_needs_details = 'Presenta signos de TDAH leve confirmados por evaluaciones privadas.'
    d_record.save()

    # DECE VISIT
    DeceVisit.objects.create(
        student=student,
        counselor=admin,
        date=timezone.now() - timezone.timedelta(days=10),
        reason='Llamado de atención por actitud disruptiva',
        observations='El estudiante se muestra ansioso, no puede mantener la atención y distrae a sus pares en las horas de Matemáticas.',
        agreements='El alumno se compromete a esforzarse en controlar su atención y sentarse en primera fila. Citación enviada a representante para reportes quincenales.'
    )

    print("Datos de prueba inyectados correctamente para el estudiante 'rmena'.")

if __name__ == '__main__':
    run()
