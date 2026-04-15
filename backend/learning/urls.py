from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, ModuleViewSet, LessonViewSet, LearningResourceViewSet, 
    EnrollmentViewSet, LessonProgressViewSet,
    QuizViewSet, QuestionViewSet, ChoiceViewSet, QuizAttemptViewSet,
    AssignmentViewSet, AssignmentSubmissionViewSet,
    DiscussionThreadViewSet, DiscussionCommentViewSet
)
from .views.calendar_views import CalendarEventsView
from .views.dashboard_views import InstructorDashboardStatsView, UnifiedSubmissionsView, InstructorExportView
from .views.category_views import CourseGroupViewSet, CourseTagViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'modules', ModuleViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'resources', LearningResourceViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'progress', LessonProgressViewSet)
router.register(r'quizzes', QuizViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'choices', ChoiceViewSet)
router.register(r'quiz-attempts', QuizAttemptViewSet)
router.register(r'assignments', AssignmentViewSet)
router.register(r'submissions', AssignmentSubmissionViewSet)
router.register(r'discussion-threads', DiscussionThreadViewSet)
router.register(r'discussion-comments', DiscussionCommentViewSet)
router.register(r'groups', CourseGroupViewSet)
router.register(r'tags', CourseTagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('calendar/events/', CalendarEventsView.as_view(), name='calendar-events'),
    path('instructor/stats/', InstructorDashboardStatsView.as_view(), name='instructor-stats'),
    path('instructor/submissions/', UnifiedSubmissionsView.as_view(), name='instructor-submissions'),
    path('instructor/export/', InstructorExportView.as_view(), name='instructor-export'),
]
