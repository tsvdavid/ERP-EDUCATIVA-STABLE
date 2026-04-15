# backend/learning/models/__init__.py
from .course import LMSCourse, LMSEnrollment, CourseGroup, CourseTag
from .structure import Module, Lesson, LearningResource
from .progress import LessonProgress
from .quizzes import Quiz, Question, Choice, QuizAttempt, AnswerSubmission
from .assignments import Assignment, AssignmentSubmission
from .discussions import DiscussionThread, DiscussionComment

__all__ = [
    'LMSCourse', 'LMSEnrollment', 'CourseGroup', 'CourseTag',
    'Module', 'Lesson', 'LearningResource',
    'LessonProgress',
    'Quiz', 'Question', 'Choice', 'QuizAttempt', 'AnswerSubmission',
    'Assignment', 'AssignmentSubmission',
    'DiscussionThread', 'DiscussionComment',
]
