# backend/learning/serializers/__init__.py
from .content import LearningResourceSerializer, LessonSerializer, ModuleSerializer
from .quiz import ChoiceSerializer, QuestionSerializer, QuizSerializer, QuizAttemptSerializer, AnswerSubmissionSerializer
from .course import CourseSerializer, EnrollmentSerializer, LessonProgressSerializer
from .assignment import AssignmentSerializer, AssignmentSubmissionSerializer
from .discussion import DiscussionThreadSerializer, DiscussionCommentSerializer

__all__ = [
    'LearningResourceSerializer', 'LessonSerializer', 'ModuleSerializer',
    'ChoiceSerializer', 'QuestionSerializer', 'QuizSerializer', 'QuizAttemptSerializer', 'AnswerSubmissionSerializer',
    'CourseSerializer', 'EnrollmentSerializer', 'LessonProgressSerializer',
    'AssignmentSerializer', 'AssignmentSubmissionSerializer',
    'DiscussionThreadSerializer', 'DiscussionCommentSerializer',
]
