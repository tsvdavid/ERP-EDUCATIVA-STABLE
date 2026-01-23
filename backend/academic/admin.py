from django.contrib import admin
from .models import Course, Subject, Enrollment, Grade, Attendance, EvaluationCategory, Observation, AcademicYear, AcademicPeriod

admin.site.register(AcademicYear)
admin.site.register(AcademicPeriod)
admin.site.register(Course)
admin.site.register(Subject)
admin.site.register(Enrollment)
admin.site.register(Grade)
admin.site.register(Attendance)
admin.site.register(EvaluationCategory)
admin.site.register(Observation)
