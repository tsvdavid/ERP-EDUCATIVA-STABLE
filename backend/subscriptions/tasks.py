from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task
def daily_subscription_check():
    """
    Se ejecuta diariamente para revisar expiraciones, cambiar estados (GRACE, SUSPENDED)
    y enviar alertas (30, 15, 7, 3, 1 días).
    """
    from subscriptions.models import Subscription, SubscriptionAuditLog
    from django.core.mail import send_mail
    from django.conf import settings
    
    today = timezone.now().date()
    
    try:
        # 1. Evaluate Expirations and Suspensions
        active_or_grace = Subscription.objects.filter(status__in=['ACTIVE', 'GRACE', 'EXPIRING'])
        
        for sub in active_or_grace:
            days_left = (sub.next_billing_date - today).days
            
            # Determine Status
            if days_left < 0:
                # Overdue
                if not sub.grace_until:
                    # Set grace period (e.g. 5 days from next_billing_date)
                    sub.grace_until = sub.next_billing_date + timedelta(days=5)
                    SubscriptionAuditLog.objects.create(
                        event_type='GRACE_ENTERED',
                        institution=sub.institution,
                        metadata_json={'next_billing_date': str(sub.next_billing_date)}
                    )
                
                if today > sub.grace_until:
                    if sub.status != 'SUSPENDED':
                        sub.status = 'SUSPENDED'
                        sub.save()
                        
                        SubscriptionAuditLog.objects.create(
                            event_type='SUSPENDED',
                            institution=sub.institution,
                            metadata_json={'reason': 'Grace period expired'}
                        )
                        
                        # Enviar correo de suspensión
                        send_mail(
                            subject=f"⚠️ Su cuenta ha sido suspendida - {sub.institution.name}",
                            message=f"Estimado usuario,\n\nSu cuenta ha sido suspendida por falta de pago. Su saldo pendiente es de ${sub.monthly_fee}.\n\nPara reactivar su servicio, comuníquese con soporte o registre su pago.",
                            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'no-reply@eduka360.com',
                            recipient_list=[sub.institution.email] if sub.institution.email else ["soporte@eduka360.com"]
                        )
                else:
                    if sub.status != 'GRACE':
                        sub.status = 'GRACE'
                        sub.save()
                        
            elif days_left <= 30:
                if sub.status != 'EXPIRING':
                    sub.status = 'EXPIRING'
                    sub.save()
                    
            # Send Alerts
            alert_days = [30, 15, 7, 3, 1]
            if days_left in alert_days:
                send_mail(
                    subject=f"Recordatorio: Su suscripción vence en {days_left} días - {sub.institution.name}",
                    message=f"Estimado usuario,\n\nLe recordamos que su suscripción vencerá el {sub.next_billing_date}. Por favor, registre su pago de ${sub.monthly_fee} para evitar interrupciones en el servicio.",
                    from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'no-reply@eduka360.com',
                    recipient_list=[sub.institution.email] if sub.institution.email else ["soporte@eduka360.com"]
                )
                SubscriptionAuditLog.objects.create(
                    event_type='EMAIL_SENT',
                    institution=sub.institution,
                    metadata_json={'days_left': days_left, 'next_billing_date': str(sub.next_billing_date)}
                )
    except Exception as e:
        SubscriptionAuditLog.objects.create(
            event_type='FAILED_TASK',
            metadata_json={'task': 'daily_subscription_check', 'error': str(e)}
        )
        raise e
            
    logger.info("Daily subscription check completed successfully.")
    return "Check complete"

@shared_task
def capture_daily_kpis():
    """
    Captura métricas de facturación diariamente para tendencias.
    """
    from subscriptions.models import Subscription, DailyKPI, SubscriptionPayment
    from django.db.models import Sum
    from django.utils import timezone
    
    today = timezone.now().date()
    
    try:
        all_subs = Subscription.objects.all()
        
        mrr = all_subs.filter(status__in=['ACTIVE', 'GRACE', 'EXPIRING']).aggregate(total=Sum('monthly_fee'))['total'] or 0
        active_count = all_subs.filter(status='ACTIVE').count()
        grace_count = all_subs.filter(status='GRACE').count()
        suspended_count = all_subs.filter(status='SUSPENDED').count()
        
        payments_today = SubscriptionPayment.objects.filter(
            payment_date__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        DailyKPI.objects.update_or_create(
            date=today,
            defaults={
                'mrr': mrr,
                'active_customers': active_count,
                'grace_count': grace_count,
                'suspended_count': suspended_count,
                'payments_today': payments_today
            }
        )
        return f"KPIs captured for {today}"
    except Exception as e:
        from subscriptions.models import SubscriptionAuditLog
        SubscriptionAuditLog.objects.create(
            event_type='FAILED_TASK',
            metadata_json={'task': 'capture_daily_kpis', 'error': str(e)}
        )
        raise e
