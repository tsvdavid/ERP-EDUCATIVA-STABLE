from django.test import TestCase
from users.models import Institution
from subscriptions.models import Subscription, Module, SubscriptionModule, SubscriptionPayment


class SubscriptionTenantChainTests(TestCase):
	def setUp(self):
		self.inst_a = Institution.objects.create(name='Inst A')
		self.inst_b = Institution.objects.create(name='Inst B')

		self.sub_a = Subscription.objects.filter(institution=self.inst_a).first()
		if not self.sub_a:
			self.sub_a = Subscription.objects.create(
				institution=self.inst_a,
				status='ACTIVE',
				start_date='2026-01-01',
				next_billing_date='2026-02-01',
				monthly_fee='10.00',
			)

		self.sub_b = Subscription.objects.filter(institution=self.inst_b).first()
		if not self.sub_b:
			self.sub_b = Subscription.objects.create(
				institution=self.inst_b,
				status='ACTIVE',
				start_date='2026-01-01',
				next_billing_date='2026-02-01',
				monthly_fee='20.00',
			)

		self.mod = Module.objects.create(code='academic', name='Academic')
		SubscriptionModule.objects.create(subscription=self.sub_a, module=self.mod)
		SubscriptionModule.objects.create(subscription=self.sub_b, module=self.mod)

		SubscriptionPayment.objects.create(subscription=self.sub_a, amount='5.00')
		SubscriptionPayment.objects.create(subscription=self.sub_b, amount='7.50')

	def test_subscription_module_can_be_resolved_by_institution_chain(self):
		qs_a = SubscriptionModule.objects.filter(subscription__institution=self.inst_a)
		qs_b = SubscriptionModule.objects.filter(subscription__institution=self.inst_b)
		self.assertEqual(qs_a.count(), 1)
		self.assertEqual(qs_b.count(), 1)

	def test_subscription_payment_can_be_resolved_by_institution_chain(self):
		qs_a = SubscriptionPayment.objects.filter(subscription__institution=self.inst_a)
		qs_b = SubscriptionPayment.objects.filter(subscription__institution=self.inst_b)
		self.assertEqual(qs_a.count(), 1)
		self.assertEqual(qs_b.count(), 1)
