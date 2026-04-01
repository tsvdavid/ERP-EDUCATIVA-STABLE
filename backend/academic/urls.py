from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, 
    SubjectViewSet, 
    EnrollmentViewSet, 
    GradeViewSet, 
    AttendanceViewSet,
    EvaluationCategoryViewSet,
    AcademicYearViewSet,
    AcademicPeriodViewSet,
    ClassScheduleViewSet
)

router = DefaultRouter()
router.register(r'academic-years', AcademicYearViewSet)
router.register(r'academic-periods', AcademicPeriodViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'evaluation-categories', EvaluationCategoryViewSet)
router.register(r'schedules', ClassScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
