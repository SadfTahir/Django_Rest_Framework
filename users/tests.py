from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from .services import issue_tokens

User = get_user_model()

SIGNUP_URL = '/api/v1/user/signup/'
LOGIN_URL = '/api/v1/user/login/'
ME_URL = '/api/v1/user/'
REFRESH_URL = '/api/v1/user/token/refresh/'
PASSWORD = 'Str0ng-pass!'


class AuthTestCase(APITestCase):
    def setUp(self):
        cache.clear()  # reset rate-limit counters between tests


class SignupTests(AuthTestCase):
    def signup(self, **overrides):
        payload = {
            'email': 'alice@example.com', 'password': PASSWORD, 'password_confirm': PASSWORD,
            'first_name': 'Alice', 'last_name': 'Smith',
        }
        payload.update(overrides)
        return self.client.post(SIGNUP_URL, payload, format='json')

    def test_signup_creates_user_and_returns_tokens(self):
        res = self.signup()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data['user']['email'], 'alice@example.com')
        self.assertEqual(res.data['user']['full_name'], 'Alice Smith')
        self.assertIn('access', res.data['tokens'])
        self.assertIn('refresh', res.data['tokens'])
        self.assertNotIn('password', res.data['user'])
        self.assertTrue(User.objects.get(email='alice@example.com').check_password(PASSWORD))

    def test_email_is_normalised_to_lowercase(self):
        res = self.signup(email='  Alice@Example.COM ')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data['user']['email'], 'alice@example.com')

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.signup()
        res = self.signup(email='ALICE@example.com')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['email'], ['A user with this email already exists.'])

    def test_password_mismatch(self):
        res = self.signup(password_confirm='Different-pass1!')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', res.data)

    def test_weak_password_rejected(self):
        for weak in ['short', '12345678', 'password']:
            with self.subTest(password=weak):
                res = self.signup(password=weak, password_confirm=weak)
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('password', res.data)

    def test_missing_and_invalid_fields(self):
        res = self.client.post(SIGNUP_URL, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(res.data), {'email', 'password', 'password_confirm'})

        res = self.signup(email='not-an-email')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data)

    def test_cannot_escalate_privileges(self):
        res = self.signup(is_staff=True, is_superuser=True)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        user = User.objects.get(email='alice@example.com')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_stale_token_does_not_block_signup(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer expired-or-garbage')
        self.assertEqual(self.signup().status_code, status.HTTP_201_CREATED)


class LoginTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('alice@example.com', PASSWORD)

    def login(self, email='alice@example.com', password=PASSWORD):
        return self.client.post(LOGIN_URL, {'email': email, 'password': password}, format='json')

    def test_login_returns_tokens_and_updates_last_login(self):
        res = self.login()
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertIn('access', res.data['tokens'])
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_login_email_is_case_insensitive(self):
        self.assertEqual(self.login(email='ALICE@Example.com').status_code, status.HTTP_200_OK)

    def test_wrong_password_and_unknown_email_give_same_error(self):
        wrong_password = self.login(password='wrong-pass')
        unknown_email = self.login(email='nobody@example.com')
        for res in (wrong_password, unknown_email):
            self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(res.data['detail'], 'Invalid email or password.')

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.login().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_fields(self):
        res = self.client.post(LOGIN_URL, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(set(res.data), {'email', 'password'})

    def test_access_token_works_on_protected_endpoint(self):
        access = self.login().data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_200_OK)

    def test_refresh_token_returns_new_access_token(self):
        refresh = self.login().data['tokens']['refresh']
        res = self.client.post(REFRESH_URL, {'refresh': refresh}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)

    def test_invalid_refresh_token(self):
        res = self.client.post(REFRESH_URL, {'refresh': 'garbage'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_is_rate_limited(self):
        statuses = [self.login(password='wrong').status_code for _ in range(11)]
        self.assertEqual(statuses[-1], status.HTTP_429_TOO_MANY_REQUESTS)


class CurrentUserTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('alice@example.com', PASSWORD, first_name='Alice')
        self.other = User.objects.create_user('bob@example.com', PASSWORD)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(self.user)['access']}")

    def test_requires_authentication(self):
        self.client.credentials()
        self.assertEqual(self.client.get(ME_URL).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.patch(ME_URL, {}, format='json').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_own_profile(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], 'alice@example.com')

    def test_patch_updates_profile(self):
        res = self.client.patch(ME_URL, {'first_name': 'Alicia', 'last_name': 'Jones'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data['full_name'], 'Alicia Jones')

    def test_patch_email_to_existing_one_is_rejected(self):
        res = self.client.patch(ME_URL, {'email': 'BOB@example.com'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data)

    def test_patch_own_email_with_different_case_is_allowed(self):
        res = self.client.patch(ME_URL, {'email': 'Alice@Example.com'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data['email'], 'alice@example.com')

    def test_read_only_and_sensitive_fields_are_ignored(self):
        res = self.client.patch(
            ME_URL,
            {'id': 999, 'is_staff': True, 'is_superuser': True, 'password': 'hacked-pass-1'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.id, 999)
        self.assertFalse(self.user.is_staff)
        self.assertTrue(self.user.check_password(PASSWORD))

    def test_put_and_delete_not_allowed(self):
        self.assertEqual(self.client.put(ME_URL, {}, format='json').status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(ME_URL).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class UserManagerTests(AuthTestCase):
    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user('', PASSWORD)

    def test_create_superuser_flags(self):
        admin = User.objects.create_superuser('Admin@Example.com', PASSWORD)
        self.assertEqual(admin.email, 'admin@example.com')
        self.assertTrue(admin.is_staff and admin.is_superuser)
        with self.assertRaises(ValueError):
            User.objects.create_superuser('x@example.com', PASSWORD, is_staff=False)
