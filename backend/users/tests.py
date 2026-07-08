from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from datetime import date

from core.thread_context import set_current_tenant_id, clear_current_tenant
from users.models import Institution


User = get_user_model()


class TenantUserManagerAndAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.inst_a = Institution.objects.create(name='Institution A')
        self.inst_b = Institution.objects.create(name='Institution B')

        self.password = 'Password123!'
        self.user_a = User.objects.create_user(
            username='user_a',
            password=self.password,
            institution=self.inst_a,
        )
        self.user_b = User.objects.create_user(
            username='user_b',
            password=self.password,
            institution=self.inst_b,
        )
        self.rector_b = User.objects.create_user(
            username='rector_b',
            password=self.password,
            institution=self.inst_b,
            role='RECTOR',
        )
        self.global_user = User.objects.create_superuser(
            username='global_admin',
            email='global@example.com',
            password=self.password,
        )

    def tearDown(self):
        clear_current_tenant()

    def _login(self, username, password):
        response = self.client.post(
            '/api/token/',
            {'username': username, 'password': password},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        return response.data

    def _switch(self, refresh_token, institution_id):
        response = self.client.post(
            '/api/users/token/switch/',
            {'refresh_token': refresh_token, 'institution_id': institution_id},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        return response.data

    def _auth(self, access_token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    def _academic_year_payload(self, year):
        return {
            'name': f'Year {year}',
            'year': year,
            'start_date': f'{year}-01-01',
            'end_date': f'{year}-12-31',
            'is_active': True,
            'is_closed': False,
        }

    def _user_payload(self, username):
        return {
            'username': username,
            'password': 'Password123!',
            'email': f'{username}@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'TEACHER',
        }

    def _assert_local_admin_equivalence(self, access_token):
        self._auth(access_token)

        year_create = self.client.post(
            '/api/academic/academic-years/',
            self._academic_year_payload(2035),
            format='json',
        )
        self.assertEqual(year_create.status_code, 201)
        year_id = year_create.data['id']

        year_update = self.client.patch(
            f'/api/academic/academic-years/{year_id}/',
            {'name': 'Year 2035 Updated'},
            format='json',
        )
        self.assertEqual(year_update.status_code, 200)

        year_delete = self.client.delete(f'/api/academic/academic-years/{year_id}/')
        self.assertEqual(year_delete.status_code, 204)

        user_create = self.client.post(
            '/api/users/',
            self._user_payload(f'user_{year_id}'),
            format='json',
        )
        self.assertEqual(user_create.status_code, 201)
        user_id = user_create.data['id']

        user_update = self.client.patch(
            f'/api/users/{user_id}/',
            {'first_name': 'Updated'},
            format='json',
        )
        self.assertEqual(user_update.status_code, 200)

        user_delete = self.client.delete(f'/api/users/{user_id}/')
        self.assertEqual(user_delete.status_code, 204)

    def test_user_objects_without_tenant_returns_empty(self):
        clear_current_tenant()
        self.assertEqual(User.objects.count(), 0)

    def test_user_unscoped_returns_global_users(self):
        clear_current_tenant()
        self.assertGreaterEqual(User.objects.unscoped().count(), 2)
        self.assertEqual(
            User.objects.unscoped().filter(
                username__in=['user_a', 'user_b']
            ).count(),
            2,
        )

    def test_login_without_x_institution_id_succeeds(self):
        response = self.client.post(
            '/api/token/',
            {'username': self.user_a.username, 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_refresh_token_generates_new_access_token(self):
        login = self.client.post(
            '/api/token/',
            {'username': self.user_a.username, 'password': self.password},
            format='json',
        )
        refresh = login.data['refresh']

        response = self.client.post(
            '/api/auth/refresh/',
            {'refresh': refresh},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_switch_institution_uses_global_unscoped_access(self):
        login = self._login(self.global_user.username, self.password)
        switched = self._switch(login['refresh'], self.inst_b.id)

        token = AccessToken(switched['access'])
        self.assertEqual(token.get('role'), 'GLOBAL')
        self.assertEqual(token.get('institution_id'), self.inst_b.id)
        self.assertEqual(token.get('institution'), self.inst_b.id)
        self.assertEqual(token.get('wizard_completed'), self.inst_b.wizard_completed)

    def test_rector_and_global_switched_equivalence_on_institution_b(self):
        rector_login = self._login(self.rector_b.username, self.password)
        global_login = self._login(self.global_user.username, self.password)
        global_switched = self._switch(global_login['refresh'], self.inst_b.id)

        rector_token = AccessToken(rector_login['access'])
        switched_token = AccessToken(global_switched['access'])

        self.assertEqual(rector_token.get('institution_id'), self.inst_b.id)
        self.assertEqual(switched_token.get('institution_id'), self.inst_b.id)

        self._assert_local_admin_equivalence(rector_login['access'])
        self._assert_local_admin_equivalence(global_switched['access'])

    def test_global_switched_isolation_is_limited_to_active_institution(self):
        global_login = self._login(self.global_user.username, self.password)
        switched_b = self._switch(global_login['refresh'], self.inst_b.id)
        switched_a = self._switch(global_login['refresh'], self.inst_a.id)

        self._auth(switched_b['access'])
        users_b = self.client.get('/api/users/')
        self.assertEqual(users_b.status_code, 200)
        usernames_b = {row['username'] for row in users_b.data}
        self.assertIn('user_b', usernames_b)
        self.assertNotIn('user_a', usernames_b)

        institutions_b = self.client.get('/api/users/institutions/')
        self.assertEqual(institutions_b.status_code, 200)
        institution_ids_b = {row['id'] for row in institutions_b.data}
        self.assertEqual(institution_ids_b, {self.inst_b.id})

        self._auth(switched_a['access'])
        users_a = self.client.get('/api/users/')
        self.assertEqual(users_a.status_code, 200)
        usernames_a = {row['username'] for row in users_a.data}
        self.assertIn('user_a', usernames_a)
        self.assertNotIn('user_b', usernames_a)

        institutions_a = self.client.get('/api/users/institutions/')
        self.assertEqual(institutions_a.status_code, 200)
        institution_ids_a = {row['id'] for row in institutions_a.data}
        self.assertEqual(institution_ids_a, {self.inst_a.id})

    def test_user_isolation_between_institutions(self):
        set_current_tenant_id(self.inst_a.id)
        users_a = list(User.objects.values_list('username', flat=True))
        self.assertIn('user_a', users_a)
        self.assertNotIn('user_b', users_a)

        set_current_tenant_id(self.inst_b.id)
        users_b = list(User.objects.values_list('username', flat=True))
        self.assertIn('user_b', users_b)
        self.assertNotIn('user_a', users_b)
