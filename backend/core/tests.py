from django.test import TestCase
from core.thread_context import set_current_tenant_id, clear_current_tenant, get_current_tenant_id
from users.models import Institution
from treasury.models import PaymentMethod


class TenantManagerTests(TestCase):
    def setUp(self):
        self.inst_a = Institution.objects.create(name='Institution A')
        self.inst_b = Institution.objects.create(name='Institution B')

        self.payment_a = PaymentMethod.objects.create(
            name='Payment A', code='PAYA', institution=self.inst_a
        )
        self.payment_b = PaymentMethod.objects.create(
            name='Payment B', code='PAYB', institution=self.inst_b
        )

    def tearDown(self):
        clear_current_tenant()

    def test_queryset_filters_by_current_tenant(self):
        set_current_tenant_id(self.inst_a.id)
        qs = PaymentMethod.objects.all()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().institution_id, self.inst_a.id)

    def test_queryset_with_nonexistent_tenant_returns_empty(self):
        set_current_tenant_id(999999)
        self.assertEqual(PaymentMethod.objects.count(), 0)

    def test_queryset_without_tenant_context_returns_empty(self):
        clear_current_tenant()
        self.assertEqual(PaymentMethod.objects.count(), 0)

    def test_unscoped_returns_global_queryset(self):
        clear_current_tenant()
        self.assertGreaterEqual(PaymentMethod.objects.unscoped().count(), 2)
        self.assertGreaterEqual(PaymentMethod.objects.global_queryset().count(), 2)
        self.assertEqual(
            PaymentMethod.objects.unscoped().filter(
                id__in=[self.payment_a.id, self.payment_b.id]
            ).count(),
            2,
        )

    def test_clear_current_tenant_resets_context(self):
        set_current_tenant_id(self.inst_a.id)
        self.assertEqual(get_current_tenant_id(), self.inst_a.id)
        clear_current_tenant()
        self.assertIsNone(get_current_tenant_id())
