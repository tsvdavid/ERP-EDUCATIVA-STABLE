from rest_framework import serializers
from ..models import Quiz, Question, Choice, QuizAttempt, AnswerSubmission
from django.db import transaction

class ChoiceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']

class QuestionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    choices = ChoiceSerializer(many=True)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'points', 'order', 'choices']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'module', 'title', 'description', 'passing_score', 
            'time_limit_minutes', 'is_active', 'created_at', 'questions'
        ]

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        with transaction.atomic():
            quiz = Quiz.objects.create(**validated_data)
            for q_data in questions_data:
                choices_data = q_data.pop('choices', [])
                question = Question.objects.create(quiz=quiz, **q_data)
                for c_data in choices_data:
                    Choice.objects.create(question=question, **c_data)
        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', [])
        with transaction.atomic():
            # Update quiz fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Handle questions
            keep_questions = []
            for q_data in questions_data:
                q_id = q_data.get('id')
                choices_data = q_data.pop('choices', [])
                
                if q_id:
                    question = Question.objects.get(id=q_id, quiz=instance)
                    for attr, value in q_data.items():
                        setattr(question, attr, value)
                    question.save()
                else:
                    question = Question.objects.create(quiz=instance, **q_data)
                
                keep_questions.append(question.id)

                # Handle choices
                keep_choices = []
                for c_data in choices_data:
                    c_id = c_data.get('id')
                    if c_id:
                        choice = Choice.objects.get(id=c_id, question=question)
                        for attr, value in c_data.items():
                            setattr(choice, attr, value)
                        choice.save()
                    else:
                        choice = Choice.objects.create(question=question, **c_data)
                    keep_choices.append(choice.id)
                
                # Delete removed choices
                Choice.objects.filter(question=question).exclude(id__in=keep_choices).delete()

            # Delete removed questions
            Question.objects.filter(quiz=instance).exclude(id__in=keep_questions).delete()

        return instance

class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = '__all__'

class AnswerSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerSubmission
        fields = '__all__'
