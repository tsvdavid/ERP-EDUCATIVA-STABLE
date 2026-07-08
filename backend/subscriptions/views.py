from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.db import transaction

from .models import Subscription, SubscriptionPayment, Module, SubscriptionAuditLog, Plan, GlobalSettings
from .serializers import SubscriptionListSerializer, SubscriptionDetailSerializer, PlanSerializer, GlobalSettingsSerializer

PLAN_MODULE_CATALOG_CODES = [
    'academic',
    'portal_digital',
    'administrative',
    'health_wellbeing',
    'payroll_rrhh',
    'accounting',
    'sales',
    'purchases',
    'help',
    'privacy',
    'maintenance',
    'saas_management',
]

class IsGlobalAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or getattr(request.user, 'role', None) == 'GLOBAL')
        )

class PlanViewSet(viewsets.ModelViewSet):
    permission_classes = [IsGlobalAdmin]
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    @action(detail=False, methods=['get'], url_path='modules-catalog')
    def modules_catalog(self, request):
        from .serializers import ModuleSerializer

        qs = Module.objects.filter(code__in=PLAN_MODULE_CATALOG_CODES)
        # Keep compatibility if an is_active field is added in the future.
        if any(f.name == 'is_active' for f in Module._meta.fields):
            qs = qs.filter(is_active=True)
        return Response(ModuleSerializer(qs.order_by('name'), many=True).data)

class GlobalSettingsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsGlobalAdmin]
    queryset = GlobalSettings.objects.all()
    serializer_class = GlobalSettingsSerializer

    def get_object(self):
        obj, created = GlobalSettings.objects.get_or_create(id=1)
        return obj

    @action(detail=False, methods=['get'])
    def current(self, request):
        obj = self.get_object()
        return Response(GlobalSettingsSerializer(obj).data)

class SubscriptionAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsGlobalAdmin]
    queryset = Subscription.objects.all().select_related('institution', 'plan').prefetch_related('modules__module')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubscriptionDetailSerializer
        return SubscriptionListSerializer

    def perform_create(self, serializer):
        data = self.request.data
        status = data.get('status', 'ACTIVE')
        start_date = serializer.validated_data.get('start_date', timezone.now().date())
        
        # Trial logic
        if status == 'TRIAL_ACTIVE':
            trial_days = int(data.get('trial_duration_days', 30))
            next_billing = start_date + timedelta(days=trial_days)
            expiration = next_billing
        else:
            # Paid logic
            months = int(data.get('contract_duration_months', 1))
            next_billing = serializer.validated_data.get('next_billing_date')
            if not next_billing:
                next_billing = start_date + timedelta(days=30)
            expiration = start_date + timedelta(days=30 * months) # Approximation
        
        subscription = serializer.save(
            next_billing_date=next_billing,
            expiration_date=expiration,
            status=status
        )
        
        # Log creation
        SubscriptionAuditLog.objects.create(
            subscription=subscription,
            event_type='PLAN_CHANGED',
            user=self.request.user,
            metadata_json={'action': 'initial_setup', 'status': status}
        )

    @action(detail=True, methods=['post'], url_path='convert-trial')
    def convert_trial(self, request, pk=None):
        subscription = self.get_object()
        if subscription.status != 'TRIAL_ACTIVE':
            return Response({'error': 'Subscription is not in trial'}, status=400)
        
        subscription.status = 'ACTIVE'
        # Reset billing to today + 30 days usually
        subscription.start_date = timezone.now().date()
        subscription.next_billing_date = subscription.start_date + timedelta(days=30)
        subscription.save()
        
        SubscriptionAuditLog.objects.create(
            subscription=subscription,
            event_type='PAYMENT_CONFIRMED',
            user=request.user,
            metadata_json={'action': 'trial_converted'}
        )
        return Response({'status': 'converted'})

    @action(detail=False, methods=['get'], url_path='institutions-without-sub')
    def institutions_without_sub(self, request):
        from .models import Institution
        institutions = Institution.objects.filter(subscription__isnull=True)
        data = [{'id': inst.id, 'name': inst.name} for inst in institutions]
        return Response(data)

    @action(detail=False, methods=['get'])
    def modules(self, request):
        from .serializers import ModuleSerializer
        institution = getattr(request, "tenant", None)
        if not institution:
            return Response([], status=200)
        subscription = (
            Subscription.objects.select_related('plan')
            .prefetch_related('plan__included_modules')
            .filter(institution=institution, status='ACTIVE')
            .first()
        )
        if not subscription or not subscription.plan_id:
            return Response([], status=200)
        qs = subscription.plan.included_modules.all().order_by('name')
        return Response(ModuleSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        # ... existing dashboard code ...
        today = timezone.now().date()
        in_15_days = today + timedelta(days=15)
        all_subs = Subscription.objects.all()
        active_customers = all_subs.filter(status__in=['ACTIVE', 'GRACE', 'EXPIRING']).count()
        expiring_soon = all_subs.filter(next_billing_date__lte=in_15_days, next_billing_date__gte=today).count()
        overdue = all_subs.filter(status__in=['GRACE', 'SUSPENDED']).count()
        mrr = all_subs.filter(status__in=['ACTIVE', 'GRACE', 'EXPIRING']).aggregate(total=Sum('monthly_fee'))['total'] or 0
        expiring_list = all_subs.filter(next_billing_date__lte=in_15_days, next_billing_date__gte=today).select_related('institution', 'plan')
        expiring_data = [{
            'id': sub.id,
            'institution_name': sub.institution.name,
            'plan_name': sub.plan.name if sub.plan else 'Sin Plan',
            'next_billing_date': sub.next_billing_date,
            'monthly_fee': sub.monthly_fee
        } for sub in expiring_list]
        overdue_list = all_subs.filter(status__in=['GRACE', 'SUSPENDED']).select_related('institution', 'plan')
        overdue_data = [{
            'id': sub.id,
            'institution_name': sub.institution.name,
            'status': sub.status,
            'next_billing_date': sub.next_billing_date,
            'monthly_fee': sub.monthly_fee
        } for sub in overdue_list]

        return Response({
            'mrr': float(mrr),
            'active_customers': active_customers,
            'expiring_soon': expiring_soon,
            'overdue': overdue,
            'expiring_list': expiring_data,
            'overdue_list': overdue_data
        })

    @action(detail=True, methods=['post'], url_path='confirm-payment')
    def confirm_payment(self, request, pk=None):
        try:
            subscription = self.get_object()
            amount = request.data.get('amount')
            notes = request.data.get('notes', '')
            months_to_extend = int(request.data.get('months_to_extend', 1))
            
            if not amount:
                return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)
                
            recent_payment = SubscriptionPayment.objects.filter(
                subscription=subscription,
                amount=amount,
                payment_date__gte=timezone.now() - timedelta(minutes=2)
            ).exists()
            
            if recent_payment:
                SubscriptionAuditLog.objects.create(
                    event_type='PAYMENT_ANOMALY',
                    institution=subscription.institution,
                    user=request.user,
                    metadata_json={'error': 'Duplicate payment detected', 'amount': str(amount)}
                )
                return Response({'error': 'Duplicate payment detected. Please wait before retrying.'}, status=status.HTTP_400_BAD_REQUEST)
                
            payment = SubscriptionPayment.objects.create(
                subscription=subscription,
                amount=amount,
                notes=notes,
                recorded_by=request.user
            )
            
            SubscriptionAuditLog.objects.create(
                event_type='PAYMENT_CONFIRMED',
                institution=subscription.institution,
                user=request.user,
                metadata_json={'amount': str(amount), 'payment_id': payment.id}
            )
            
            subscription.next_billing_date = subscription.next_billing_date + timedelta(days=30 * months_to_extend)
            subscription.status = 'ACTIVE'
            subscription.grace_until = None
            subscription.save()
            
            return Response({'message': 'Pago confirmado y suscripción extendida.'})
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        sub = self.get_object()
        sub.status = 'SUSPENDED'
        sub.suspended_at = timezone.now()
        sub.save()
        SubscriptionAuditLog.objects.create(
            event_type='SUSPENDED',
            institution=sub.institution,
            user=request.user,
            metadata_json={'reason': request.data.get('reason', 'Suspensión manual por administrador')}
        )
        return Response({'message': 'Suscripción suspendida manualmente.'})

    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        sub = self.get_object()
        sub.status = 'ACTIVE'
        sub.suspended_at = None
        sub.save()
        SubscriptionAuditLog.objects.create(
            event_type='PAYMENT_CONFIRMED', # Using payment confirm code for simplicity or add a new one
            institution=sub.institution,
            user=request.user,
            metadata_json={'action': 'Reactivación manual'}
        )
        return Response({'message': 'Suscripción reactivada manualmente.'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        sub = self.get_object()
        sub.status = 'CANCELLED'
        sub.cancelled_at = timezone.now()
        sub.save()
        SubscriptionAuditLog.objects.create(
            event_type='FAILED_TASK', # Add better codes later
            institution=sub.institution,
            user=request.user,
            metadata_json={'action': 'Cancelación manual'}
        )
        return Response({'message': 'Suscripción cancelada permanentemente.'})
    
    @action(detail=True, methods=['post', 'patch'], url_path='change-plan')
    def change_plan(self, request, pk=None):
        sub = self.get_object()
        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response({'success': False, 'message': 'plan_id es requerido'}, status=400)

        raw_apply_modules = request.data.get('apply_modules', True)
        if isinstance(raw_apply_modules, str):
            apply_modules = raw_apply_modules.strip().lower() in ('1', 'true', 'yes', 'on')
        else:
            apply_modules = bool(raw_apply_modules)

        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response({'success': False, 'message': 'Plan no encontrado o inactivo'}, status=404)

        if not sub.institution_id:
            return Response({'success': False, 'message': 'La suscripción no tiene institución válida'}, status=400)

        old_plan_name = sub.plan.name if sub.plan else None
        old_plan_id = sub.plan_id
        old_module_ids = list(sub.plan.included_modules.values_list('id', flat=True)) if sub.plan_id else []

        if old_plan_id == plan.id:
            return Response({
                'success': True,
                'message': 'La suscripción ya tiene ese plan.',
                'subscription': SubscriptionListSerializer(sub).data,
            }, status=200)

        cycle_days = {
            'MONTHLY': 30,
            'QUARTERLY': 90,
            'SEMIANNUAL': 180,
            'YEARLY': 365,
        }

        with transaction.atomic():
            sub.plan = plan
            sub.monthly_fee = plan.base_price_monthly

            if sub.next_billing_date and sub.next_billing_date < timezone.now().date():
                sub.next_billing_date = timezone.now().date() + timedelta(
                    days=cycle_days.get(sub.billing_cycle, 30)
                )

            sub.save(update_fields=['plan', 'monthly_fee', 'next_billing_date', 'updated_at'])

            # Keep compatibility with existing payloads. Enabled modules are
            # now derived from plan.included_modules and not persisted per subscription.
            new_module_ids = list(plan.included_modules.values_list('id', flat=True))

            SubscriptionAuditLog.objects.create(
                event_type='PLAN_CHANGED',
                institution=sub.institution,
                user=request.user,
                metadata_json={
                    'action': 'change_plan',
                    'subscription_id': sub.id,
                    'old_plan_id': old_plan_id,
                    'old_plan_name': old_plan_name,
                    'new_plan_id': plan.id,
                    'new_plan_name': plan.name,
                    'apply_modules': apply_modules,
                    'old_module_ids': old_module_ids,
                    'new_module_ids': new_module_ids,
                    'changed_at': timezone.now().isoformat(),
                }
            )

        sub.refresh_from_db()
        return Response({
            'success': True,
            'message': 'Plan actualizado correctamente',
            'subscription': SubscriptionListSerializer(sub).data,
        })

    @action(detail=True, methods=['post'], url_path='edit-dates')
    def edit_dates(self, request, pk=None):
        sub = self.get_object()
        next_billing_date = request.data.get('next_billing_date')
        if next_billing_date:
            sub.next_billing_date = next_billing_date
            sub.save()
            SubscriptionAuditLog.objects.create(
                event_type='PAYMENT_CONFIRMED',
                institution=sub.institution,
                user=request.user,
                metadata_json={'action': 'Ajuste de fecha manual', 'new_date': next_billing_date}
            )
            return Response({'message': 'Fecha de facturación actualizada.'})
        return Response({'error': 'next_billing_date es requerida'}, status=400)

    @action(detail=True, methods=['post'], url_path='update-modules')
    def update_modules(self, request, pk=None):
        return Response(
            {
                'message': (
                    'La personalización de módulos por suscripción fue deshabilitada. '
                    'Configure módulos en el plan y cambie el plan de la suscripción.'
                ),
                'code': 'MODULE_OVERRIDE_DISABLED',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

class ObservabilityViewSet(viewsets.ViewSet):
    permission_classes = [IsGlobalAdmin]

    @action(detail=False, methods=['get'])
    def monitoring(self, request):
        from .models import SubscriptionAuditLog, DailyKPI, Subscription
        from django.db.models import Sum
        
        # 1. Trend Chart (last 30 days)
        kpis = DailyKPI.objects.all()[:30]
        trend_data = [{
            'date': str(kpi.date),
            'mrr': float(kpi.mrr),
            'active': kpi.active_customers,
            'payments': float(kpi.payments_today)
        } for kpi in reversed(kpis)]
        
        # 2. Recent Activity (last 50 logs)
        logs = SubscriptionAuditLog.objects.select_related('institution', 'user').order_by('-created_at')[:50]
        activity_data = [{
            'id': log.id,
            'event': log.get_event_type_display(),
            'event_code': log.event_type,
            'institution': log.institution.name if log.institution else 'Global',
            'user': log.user.username if log.user else 'System',
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M'),
            'metadata': log.metadata_json
        } for log in logs]
        
        # 3. Anomalies & Failed Tasks
        alerts = SubscriptionAuditLog.objects.filter(
            event_type__in=['PAYMENT_ANOMALY', 'FAILED_TASK']
        ).order_by('-created_at')[:10]
        alert_data = [{
            'event': log.get_event_type_display(),
            'metadata': log.metadata_json,
            'created_at': log.created_at.strftime('%Y-%m-%d %H:%M')
        } for log in alerts]
        
        # 4. Suspended Customers List
        suspended = Subscription.objects.filter(status='SUSPENDED').select_related('institution')
        suspended_data = [{
            'institution': sub.institution.name,
            'next_billing_date': str(sub.next_billing_date),
            'monthly_fee': float(sub.monthly_fee)
        } for sub in suspended]

        return Response({
            'trend_chart': trend_data,
            'audit_logs': activity_data,
            'alerts': alert_data,
            'suspended_customers': suspended_data
        })

class MySubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='info')
    def info(self, request):
        """Return billing info for the institution resolved from the request.
        The tenant resolution follows:
        1) X-Institution-ID header
        2) JWT claim ``institution`` (or ``institution_id``)
        3) request.user.institution (fallback)
        """
        from core.tenancy.utils import get_current_institution
        # Resolve the institution for this request
        institution = get_current_institution(request)
        if not institution:
            return Response({
                'error': 'Institution not resolved from request.'
            }, status=400)
        try:
            sub = institution.subscription
        except Subscription.DoesNotExist:
            return Response({
                'error': 'No hay suscripción activa para esta institución.'
            }, status=404)
        modules = sub.plan.included_modules.all().order_by('name') if sub.plan_id else []
        return Response({
            'id': sub.id,
            'institution': institution.name,
            'status': sub.status,
            'next_billing_date': sub.next_billing_date,
            'grace_until': sub.grace_until,
            'monthly_fee': float(sub.monthly_fee),
            'plan_name': sub.plan.name if sub.plan else 'Personalizado',
            'modules': [m.name for m in modules],
            'module_codes': [m.code for m in modules],
            'payment_instructions': "Para renovar su suscripción, por favor realice un depósito o transferencia a la Cuenta Corriente N° 123456789 del Banco Pichincha a nombre de Eduka360 S.A. y envíe el comprobante a facturacion@eduka360.com."
        })
