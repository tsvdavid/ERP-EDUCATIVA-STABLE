from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Assignment, Lesson, LMSEnrollment
from communication.models import Holiday, Notice
from django.db.models import Q
from django.utils import timezone

class CalendarEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        events = []

        # 1. Tareas (Assignments)
        assignments_qs = Assignment.objects.all()
        if user.role == 'STUDENT':
            enr_course_ids = LMSEnrollment.objects.filter(user=user).values_list('course_id', flat=True)
            assignments_qs = assignments_qs.filter(module__course_id__in=enr_course_ids)
        elif user.role == 'TEACHER':
            assignments_qs = assignments_qs.filter(module__course__instructor=user)
        
        for a in assignments_qs:
            if a.due_date:
                events.append({
                    'id': f"assignment_{a.id}",
                    'title': a.title,
                    'start': a.due_date,
                    'type': 'assignment',
                    'color': '#f59e0b', # Amber
                    'url': f"/dashboard/campus-virtual/player/{a.module.course_id}",
                    'course_name': a.module.course.title
                })

        # 2. Clases en Vivo (Live Sessions)
        lessons_qs = Lesson.objects.exclude(meeting_url__isnull=True).exclude(meeting_url='')
        if user.role == 'STUDENT':
            enr_course_ids = LMSEnrollment.objects.filter(user=user).values_list('course_id', flat=True)
            lessons_qs = lessons_qs.filter(module__course_id__in=enr_course_ids)
        elif user.role == 'TEACHER':
            lessons_qs = lessons_qs.filter(module__course__instructor=user)

        for l in lessons_qs:
            if l.meeting_date:
                events.append({
                    'id': f"lesson_{l.id}",
                    'title': f"Clase: {l.title}",
                    'start': l.meeting_date,
                    'type': 'meeting',
                    'color': '#6366f1', # Indigo
                    'url': f"/dashboard/campus-virtual/player/{l.module.course_id}",
                    'course_name': l.module.course.title
                })

        # 3. Feriados (Holidays)
        holidays_qs = Holiday.objects.all()
        for h in holidays_qs:
            # Convert date to datetime for consistency if needed, or just ISO string
            events.append({
                'id': f"holiday_{h.id}",
                'title': f"Feriado: {h.name}",
                'start': h.date.isoformat(),
                'type': 'holiday',
                'color': '#ef4444', 
                'description': h.description or 'Feriado Nacional'
            })

        # 4. Avisos Institucionales con fecha
        notices_qs = Notice.objects.exclude(event_date__isnull=True)
        for n in notices_qs:
            events.append({
                'id': f"notice_{n.id}",
                'title': n.title,
                'start': n.event_date,
                'type': 'notice',
                'color': '#10b981',
                'description': n.content[:200]
            })

        return Response(events)
