from django.utils import timezone
from datetime import timedelta


def calculate_risk_profile(student, academic_year):
    from .models import BehaviorRecord, BehaviorCase, StudentRiskProfile
    now = timezone.now()
    records_qs = BehaviorRecord.objects.filter(student=student, academic_year=academic_year)
    positives = records_qs.filter(record_type='POSITIVE').count()
    neg_mild = records_qs.filter(record_type='NEGATIVE_MILD').count()
    neg_severe = records_qs.filter(record_type='NEGATIVE_SEVERE').count()
    total_neg = neg_mild + (neg_severe * 2)
    neg_7d = records_qs.filter(created_at__gte=now - timedelta(days=7)).exclude(record_type='POSITIVE').count()
    behavior_score = max(0.0, min(100.0, 100.0 - (total_neg * 8) + (positives * 3)))
    try:
        from academic.models import Attendance
        total = Attendance.objects.filter(student=student, academic_year=academic_year).count()
        present = Attendance.objects.filter(student=student, academic_year=academic_year, status='PRESENT').count()
        attendance_score = (present / total * 100) if total > 0 else 100.0
    except Exception:
        attendance_score = 100.0
    try:
        from academic.models import Grade
        grades = list(Grade.objects.filter(student=student, academic_year=academic_year).values_list('score', flat=True))
        academic_score = min(100.0, max(0.0, (sum(grades)/len(grades)/10.0)*100)) if grades else 100.0
    except Exception:
        academic_score = 100.0
    has_open = BehaviorCase.objects.filter(student=student, academic_year=academic_year, status__in=['OPEN','IN_PROGRESS']).exists()
    worst = min(behavior_score, attendance_score, academic_score)
    if worst >= 70 and not has_open:
        risk = 'GREEN'
    elif worst >= 40:
        risk = 'YELLOW'
    else:
        risk = 'RED'
    profile, _ = StudentRiskProfile.objects.update_or_create(
        student=student, academic_year=academic_year,
        defaults={'behavior_score': round(behavior_score,1), 'attendance_score': round(attendance_score,1),
                  'academic_score': round(academic_score,1), 'overall_risk': risk,
                  'negative_count_7d': neg_7d, 'has_open_case': has_open}
    )
    return profile


def evaluate_alert_rules(student, institution, academic_year):
    from .models import AlertRule, BehaviorRecord, BehaviorCase
    now = timezone.now()
    triggered_cases = []
    for rule in AlertRule.objects.filter(institution=institution, is_active=True):
        window_start = now - timedelta(days=rule.days_window)
        neg_qs = BehaviorRecord.objects.filter(
            student=student, academic_year=academic_year,
            created_at__gte=window_start, record_type__in=['NEGATIVE_MILD','NEGATIVE_SEVERE']
        )
        count = neg_qs.count()
        triggers = count >= rule.negative_count_threshold
        if rule.include_low_grades and not triggers:
            try:
                from academic.models import Grade
                if Grade.objects.filter(student=student, academic_year=academic_year, score__lt=rule.grade_threshold).count() >= 2:
                    triggers = True
            except Exception:
                pass
        if rule.include_absences and not triggers:
            try:
                from academic.models import Attendance
                if Attendance.objects.filter(student=student, academic_year=academic_year, status='ABSENT').count() >= rule.absence_threshold:
                    triggers = True
            except Exception:
                pass
        if triggers and rule.auto_create_case:
            if not BehaviorCase.objects.filter(student=student, academic_year=academic_year, area=rule.target_area, status__in=['OPEN','IN_PROGRESS']).exists():
                case = BehaviorCase.objects.create(
                    student=student, academic_year=academic_year, area=rule.target_area,
                    status='OPEN', priority='HIGH',
                    title=f"Alerta automática: {rule.name}",
                    description=f"Caso generado por regla '{rule.name}'. {count} observaciones negativas en {rule.days_window} días.",
                )
                case.behavior_records.set(neg_qs[:10])
                neg_qs.update(triggered_alert=True)
                triggered_cases.append(case)
    calculate_risk_profile(student, academic_year)
    return triggered_cases
