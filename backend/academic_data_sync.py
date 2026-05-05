from academic.models import AcademicPeriod, Subject, Enrollment, EvaluationCategory, Grade, Attendance, ClassSchedule
from django.db import transaction

def sync_academic():
    with transaction.atomic():
        print("Sincronizando AcademicPeriod...")
        for obj in AcademicPeriod.objects.filter(institution__isnull=True):
            obj.institution = obj.academic_year.institution
            obj.save()
            
        print("Sincronizando Subject...")
        for obj in Subject.objects.filter(institution__isnull=True):
            obj.institution = obj.course.institution
            obj.save()
            
        print("Sincronizando Enrollment...")
        for obj in Enrollment.objects.filter(institution__isnull=True):
            # Asignamos la institución del curso (que ya es TenantModel)
            obj.institution = obj.course.institution
            obj.save()
            
        print("Sincronizando EvaluationCategory...")
        for obj in EvaluationCategory.objects.filter(institution__isnull=True):
            obj.institution = obj.subject.institution
            obj.save()
            
        print("Sincronizando Grade...")
        for obj in Grade.objects.filter(institution__isnull=True):
            obj.institution = obj.enrollment.institution
            obj.save()
            
        print("Sincronizando Attendance...")
        for obj in Attendance.objects.filter(institution__isnull=True):
            obj.institution = obj.enrollment.institution
            obj.save()
            
        print("Sincronizando ClassSchedule...")
        for obj in ClassSchedule.objects.filter(institution__isnull=True):
            obj.institution = obj.subject.institution
            obj.save()
            
    print("Sincronización de Academic completada.")

if __name__ == "__main__":
    sync_academic()
