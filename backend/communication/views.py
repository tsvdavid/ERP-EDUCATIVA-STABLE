from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from .models import Message, Notification, Notice, Holiday
from .serializers import (
    MessageSerializer, NotificationSerializer, 
    NoticeSerializer, HolidaySerializer
)
from users.permissions import IsAdminOrLocalAdminUser, IsTeacherUser, IsRectorUser

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Message.objects.filter(Q(recipient=user) | Q(sender=user))
        
        # Security: Enforce Institution (though messages are user-to-user, users are in institution)
        # Assuming users can only message within their institution (or global?)
        # For now, rely on user visibility restrictions (UserViewSet) to prevent messaging cross-institution users.
        return queryset

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Mensajes recibidos"""
        messages = Message.objects.filter(recipient=request.user, parent=None).order_by('-created_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Mensajes enviados"""
        messages = Message.objects.filter(sender=request.user, parent=None).order_by('-created_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Notifications are strictly per user, so they are implicitly isolated.
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'read'})

class NoticeViewSet(viewsets.ModelViewSet):
    serializer_class = NoticeSerializer
    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):
        user = self.request.user
        queryset = Notice.objects.all()
        
        # 0. Strict Institution Filter
        if user.institution:
             # Filter based on author's institution OR target course's institution
             # Best: Filter where author is in the same institution
             queryset = queryset.filter(Q(author__institution=user.institution) | Q(author__institution__isnull=True))
             
        if user.role == 'ADMIN' or user.role == 'RECTOR':
             return queryset.order_by('-created_at')

        # Logic for Teachers/Students/Parents
        if user.role == 'STUDENT':
            # Get student's course
            from academic.models import Enrollment
            student_courses = Enrollment.objects.filter(student=user).values_list('course', flat=True)
            
            queryset = queryset.filter(
                # 1. Specifically targeted to this student
                Q(target_students=user) |
                
                # 2. Targeted to the student's course (and role matches)
                (Q(target_course__in=student_courses) & Q(target_role__in=['ALL', 'STUDENT'])) |
                
                # 3. Global announcement (No course, No specific students)
                (Q(target_course__isnull=True) & Q(target_students__isnull=True) & Q(target_role__in=['ALL', 'STUDENT']))
            ).distinct()

        elif user.role == 'TEACHER':
            # Teachers see:
            # 1. Notes they authored
            # 2. Global announcements for Teachers/All (No course specific)
            # 3. Course announcements where they teach a subject
            
            # Get courses where this teacher teaches a subject
            from academic.models import Subject
            teacher_courses = Subject.objects.filter(teacher=user).values_list('course', flat=True)

            queryset = queryset.filter(
                Q(author=user) |
                (Q(target_course__isnull=True) & Q(target_students__isnull=True) & Q(target_role__in=['ALL', 'TEACHER'])) |
                (Q(target_course__in=teacher_courses) & Q(target_role__in=['ALL', 'TEACHER']))
            ).distinct()
            
        elif user.role == 'PARENT':
             # Parents see:
             # 1. Global announcements for Parents/All
             # 2. Course announcements for their children's course
             children = user.children.all()
             from academic.models import Enrollment
             children_courses = Enrollment.objects.filter(student__in=children).values_list('course', flat=True)

             queryset = queryset.filter(
                (Q(target_course__in=children_courses) & Q(target_role__in=['ALL', 'PARENT'])) |
                (Q(target_course__isnull=True) & Q(target_students__isnull=True) & Q(target_role__in=['ALL', 'PARENT']))
            ).distinct()

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        try:
            user = self.request.user
            # Validation
            if user.role == 'TEACHER':
                target_course = serializer.validated_data.get('target_course')
                if target_course:
                     # Check if teacher teaches any subject in this course
                     from academic.models import Subject
                     if not Subject.objects.filter(course=target_course, teacher=user).exists():
                         raise PermissionDenied("No puedes enviar avisos a cursos donde no dictas clases.")
                
                target_role = serializer.validated_data.get('target_role', 'ALL') 
                if target_role == 'ALL' or target_role == 'PARENT':
                       if not target_course and not serializer.validated_data.get('target_students'):
                           pass 

            notice = serializer.save(author=user)
            
            # Helper logic to create Notification (Alert) if requested
            if (user.role == 'ADMIN' or user.role == 'RECTOR') and self.request.data.get('create_alert') == 'true':
                from .models import Notification
                Notification.objects.create(
                    user=user, # This might need to be targeted to recipients, but usually notifications are individual. 
                               # If the requirement is "alert users", we'd need to create 1 notification per target user.
                               # For now, simplest interpretation: The notice ITSELF acts as an alert, but if they want a separate Notification object?
                               # Actually, "Alerts" in frontend seem to come from `notifications` endpoint.
                               # Let's assume this means generating system notifications for the TARGETS.
                    type=Notification.Type.ALERT,
                    priority=Notification.Priority.HIGH, # Alert implies high priority
                    title=f"Alerta: {notice.title}",
                    message=notice.content[:200], # Trucate
                    related_object_id=notice.id,
                    related_content_type='notice'
                )
                # Note: The above creates a notification for the AUTHOR? No, notifications are usually for recipients. 
                # If we want to notify ALL targets, that's a heavier operation (looping through students/teachers).
                # Given MVP, let's look at how Notifications are fetched: `Notification.objects.filter(user=self.request.user)`
                # So creating a notification for 'user=user' only notifies the creator. 
                # To notify targets, we need to iterate.
                
                targets = []
                # Simple targeting logic matching get_queryset info roughly
                from users.models import User
                from academic.models import Enrollment
                
                q = Q()
                if notice.target_role != 'ALL':
                    q &= Q(role=notice.target_role)
                
                if notice.target_course:
                    # Students in course
                    student_ids = Enrollment.objects.filter(course=notice.target_course).values_list('student', flat=True)
                    q &= Q(id__in=student_ids)
                
                if notice.target_students.exists():
                    q &= Q(id__in=notice.target_students.all())
                
                # Fetch separate list if specific filters exist, otherwise strict filtering might be too heavy for sync.
                # For this task, let's limit "Create Alert" to creating a system-wide notification (if broadcast) or specific.
                # But creating 1000 notifications in a loop is bad in main thread.
                # Alternative: The "Notifications" list in frontend IS the alerts list.
                # If the user wants it to appear in the RED section, it needs to be a Notification object.
                # Let's create it for the author to test, and maybe a few targets?
                # For safety/performance in this MVP, let's create a notification for the AUTHOR confirming it, 
                # OR if the user expects all students to see it in red... we need to create it for them.
                # Let's assume moderate usage and create for targets.
                
                target_users = User.objects.filter(q).distinct()
                notifications_to_create = [
                    Notification(
                        user=u,
                        type=Notification.Type.ALERT,
                        priority=Notification.Priority.HIGH,
                        title=notice.title,
                        message=notice.content[:200]
                    ) for u in target_users if u != user
                ]
                Notification.objects.bulk_create(notifications_to_create)

            return notice
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise ValidationError(f"Error creating alert: {str(e)}")


class HolidayViewSet(viewsets.ModelViewSet):
    serializer_class = HolidaySerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
             return [permissions.IsAuthenticated()]
        return [IsAdminOrLocalAdminUser()] # Changed from permissions.IsAdminUser()
    
    def get_queryset(self):
         # Allow all authenticated users to view
         return Holiday.objects.all().order_by('date')

    @action(detail=False, methods=['post'], permission_classes=[IsAdminOrLocalAdminUser]) # Changed from permissions.IsAdminUser
    def populate_holidays(self, request):
        """Populate holidays for Ecuador for a given year (defaults to current)"""
        import holidays
        from datetime import date
        
        year = request.data.get('year', date.today().year)
        ec_holidays = holidays.EC(years=int(year))
        
        created_count = 0
        for date_obj, name in ec_holidays.items():
             _, created = Holiday.objects.get_or_create(
                 date=date_obj,
                 defaults={
                     'name': name,
                     'description': 'Feriado Nacional (Auto-generado)',
                     'is_system': True
                 }
             )
             if created:
                 created_count += 1
                 
        return Response({'status': 'populated', 'created': created_count})
