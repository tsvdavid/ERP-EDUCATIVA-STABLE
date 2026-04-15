from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AssignmentSubmission, LessonProgress
from academic.models import Grade, Enrollment
from communication.models import Notification
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=AssignmentSubmission)
def sync_grade_to_academic(sender, instance, **kwargs):
    """
    Sincroniza la nota de una tarea del LMS con el módulo académico oficial.
    """
    assignment = instance.assignment
    
    # Solo sincronizar si hay una categoría académica vinculada y una nota asignada
    if not assignment.academic_category or instance.score is None:
        return

    try:
        # ... (rest of the sync logic remains unchanged)
        # 1. Obtener la materia académica vinculada al curso del LMS
        lms_course = assignment.module.course
        academic_subject = lms_course.subject
        
        if not academic_subject:
            return

        # 2. Obtener la matrícula del estudiante en el curso académico físico
        enrollment = Enrollment.objects.filter(
            student=instance.student,
            course=academic_subject.course
        ).first()

        if not enrollment:
            return

        # 3. Calcular la nota escalada a base 10
        scaled_score = instance.score
        if assignment.max_score > 0 and assignment.max_score != 10:
            scaled_score = round((instance.score * 10) / assignment.max_score, 2)

        # 4. Crear o actualizar el registro en el Cuaderno Académico
        Grade.objects.update_or_create(
            enrollment=enrollment,
            subject=academic_subject,
            category=assignment.academic_category,
            defaults={
                'score': scaled_score,
                'date': instance.submitted_at.date() if instance.submitted_at else timezone.now().date(),
                'description': f"Sincronizado desde LMS: {assignment.title}",
                'observation': instance.teacher_feedback or 'Sincronización automática.'
            }
        )
    except Exception as e:
        logger.error(f"Error en sincronización de notas: {str(e)}")

@receiver(post_save, sender=AssignmentSubmission)
def send_grading_notification(sender, instance, created, **kwargs):
    """
    Envía una notificación al estudiante cuando su tarea es calificada.
    """
    # Solo enviamos notificación si se ha asignado una puntuación
    if instance.score is not None:
        try:
            Notification.objects.create(
                user=instance.student,
                type=Notification.Type.NOTICE,
                priority=Notification.Priority.MEDIUM,
                title=f"Tarea Calificada: {instance.assignment.title}",
                message=f"Tu profesor ha calificado tu tarea '{instance.assignment.title}' con {instance.score}/{instance.assignment.max_score}. Revisa el feedback en tu panel.",
                related_content_type='assignment',
                related_object_id=instance.assignment.id
            )
            logger.info(f"Notificación enviada a {instance.student.username} por tarea graded.")
        except Exception as e:
            logger.error(f"Error al enviar notificación de calificación: {str(e)}")

@receiver(post_save, sender=LessonProgress)
def update_enrollment_progress(sender, instance, **kwargs):
    """
    Recalcula el porcentaje de progreso del alumno cada vez que completa una lección.
    """
    from .models import Lesson
    enrollment = instance.enrollment
    course = enrollment.course
    
    # Total de lecciones en el curso
    total_lessons = Lesson.objects.filter(module__course=course).count()
    
    if total_lessons > 0:
        # Lecciones completadas por el alumno
        completed_lessons = enrollment.lesson_progress.filter(is_completed=True).count()
        
        # Calcular porcentaje
        percentage = (completed_lessons * 100) / total_lessons
        enrollment.progress_percentage = round(percentage, 2)
        
        # Actualizar estado si es 100%
        if percentage >= 100:
            enrollment.status = 'completed'
            enrollment.is_completed = True
        
        enrollment.save(update_fields=['progress_percentage', 'status', 'is_completed'])
        logger.info(f"Progreso actualizado para {enrollment.user.username} en {course.title}: {enrollment.progress_percentage}%")
