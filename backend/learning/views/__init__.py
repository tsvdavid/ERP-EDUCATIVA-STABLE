# backend/learning/views/__init__.py
from .course_views import CourseViewSet, EnrollmentViewSet
from .content_views import ModuleViewSet, LessonViewSet, LearningResourceViewSet, LessonProgressViewSet
from .quiz_views import QuizViewSet, QuestionViewSet, ChoiceViewSet, QuizAttemptViewSet
from .assignment_views import AssignmentViewSet, AssignmentSubmissionViewSet
from .discussion_views import DiscussionThreadViewSet, DiscussionCommentViewSet

__all__ = [
    'CourseViewSet', 'EnrollmentViewSet',
    'ModuleViewSet', 'LessonViewSet', 'LearningResourceViewSet', 'LessonProgressViewSet',
    'QuizViewSet', 'QuestionViewSet', 'ChoiceViewSet', 'QuizAttemptViewSet',
    'AssignmentViewSet', 'AssignmentSubmissionViewSet',
    'DiscussionThreadViewSet', 'DiscussionCommentViewSet',
]
