import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from users.services import issue_tokens

from .models import Make, Vehicle

User = get_user_model()
MEDIA_TMP = tempfile.mkdtemp()


def tearDownModule():
    shutil.rmtree(MEDIA_TMP, ignore_errors=True)


def make_image():
    buf = BytesIO()
    Image.new('RGB', (10, 10), 'red').save(buf, 'PNG')
    return SimpleUploadedFile('logo.png', buf.getvalue(), content_type='image/png')


class AuthenticatedAPITestCase(APITestCase):
    """Logs in a user via force_authenticate for every test."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('alice@example.com', 'Str0ng-pass!')
        cls.other_user = User.objects.create_user('bob@example.com', 'Str0ng-pass!')

    def setUp(self):
        self.client.force_authenticate(self.user)


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class MakeAPITests(AuthenticatedAPITestCase):
    url = '/api/v1/make/'

    def test_crud(self):
        res = self.client.post(self.url, {'name': 'Toyota', 'founded_at': '1937-08-28', 'logo': make_image()}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertIn('make_logos/', res.data['logo'])
        pk = res.data['id']

        self.assertEqual(self.client.get(self.url).data['count'], 1)
        self.assertEqual(self.client.get(f'{self.url}{pk}/').data['name'], 'Toyota')

        res = self.client.patch(f'{self.url}{pk}/', {'name': 'Toyota Motor'}, format='json')
        self.assertEqual(res.data['name'], 'Toyota Motor')

        self.assertEqual(self.client.put(f'{self.url}{pk}/', {}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(f'{self.url}{pk}/').status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Make.objects.exists())

    def test_duplicate_name_rejected(self):
        Make.objects.create(name='Honda', founded_at='1948-09-24')
        res = self.client.post(self.url, {'name': 'Honda', 'founded_at': '1948-09-24'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', res.data)

    def test_filters(self):
        Make.objects.create(name='Honda', founded_at='1948-09-24', created_by=self.user)
        Make.objects.create(name='Ford', founded_at='1903-06-16', created_by=self.other_user)
        self.assertEqual(self.client.get(self.url, {'name': 'hon'}).data['count'], 1)
        self.assertEqual(self.client.get(self.url, {'founded_after': '1940-01-01'}).data['count'], 1)
        self.assertEqual(self.client.get(self.url, {'created_by': self.other_user.id}).data['count'], 1)


@override_settings(MEDIA_ROOT=MEDIA_TMP)
class VehicleAPITests(AuthenticatedAPITestCase):
    url = '/api/v2/vehicle/'

    def setUp(self):
        super().setUp()
        self.make = Make.objects.create(name='Honda', founded_at='1948-09-24')

    def test_crud(self):
        payload = {'make': self.make.id, 'name': 'Civic', 'model': '2024', 'color': 'Black', 'engine': 1500}
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data['make_name'], 'Honda')
        pk = res.data['id']

        res = self.client.patch(f'{self.url}{pk}/', {'color': 'White'}, format='json')
        self.assertEqual(res.data['color'], 'White')
        self.assertEqual(self.client.delete(f'{self.url}{pk}/').status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Vehicle.objects.exists())

    def test_image_in_filtered_results(self):
        payload = {'make': self.make.id, 'name': 'Civic', 'model': '2024', 'color': 'Black', 'engine': 1500, 'image': make_image()}
        res = self.client.post(self.url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertTrue(res.data['image'].startswith('http://testserver/media/vehicle_images/'))

        result = self.client.get(self.url, {'color': 'black'}).data['results'][0]
        self.assertEqual(result['image'], res.data['image'])
        vehicle = Vehicle.objects.get()
        self.assertTrue(vehicle.image.storage.exists(vehicle.image.name))

    def test_invalid_make(self):
        res = self.client.post(self.url, {'make': 999, 'name': 'X', 'model': '1', 'color': 'r', 'engine': 1}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_engine_rejected(self):
        res = self.client.post(self.url, {'make': self.make.id, 'name': 'X', 'model': '1', 'color': 'r', 'engine': -5}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('engine', res.data)

    def test_missing_record_returns_404(self):
        self.assertEqual(self.client.get(f'{self.url}999999/').status_code, status.HTTP_404_NOT_FOUND)

    def test_filters(self):
        Vehicle.objects.create(make=self.make, name='Civic', model='2024', color='Black', engine=1500)
        Vehicle.objects.create(make=self.make, name='Accord', model='2023', color='White', engine=2000)
        self.assertEqual(self.client.get(self.url, {'color': 'black'}).data['count'], 1)
        self.assertEqual(self.client.get(self.url, {'engine_min': 1800}).data['count'], 1)
        self.assertEqual(self.client.get(self.url, {'make': self.make.id}).data['count'], 2)
        self.assertEqual(self.client.get(self.url, {'search': 'accord'}).data['count'], 1)


class AuditFieldTests(AuthenticatedAPITestCase):
    vehicle_url = '/api/v2/vehicle/'

    def setUp(self):
        super().setUp()
        self.make = Make.objects.create(name='Honda', founded_at='1948-09-24')

    def test_created_by_and_updated_by_are_set_from_request_user(self):
        res = self.client.post(
            self.vehicle_url,
            {'make': self.make.id, 'name': 'Civic', 'model': '2024', 'color': 'Black', 'engine': 1500},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data['created_by']['email'], self.user.email)
        self.assertEqual(res.data['updated_by']['email'], self.user.email)

        # A different user edits the record: only updated_by changes.
        self.client.force_authenticate(self.other_user)
        res = self.client.patch(f"{self.vehicle_url}{res.data['id']}/", {'color': 'Red'}, format='json')
        self.assertEqual(res.data['created_by']['email'], self.user.email)
        self.assertEqual(res.data['updated_by']['email'], self.other_user.email)

    def test_client_cannot_set_audit_fields(self):
        res = self.client.post(
            self.vehicle_url,
            {'make': self.make.id, 'name': 'Civic', 'model': '2024', 'color': 'Black', 'engine': 1500,
             'created_by': self.other_user.id, 'updated_by': self.other_user.id},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(res.data['created_by']['id'], self.user.id)
        self.assertEqual(res.data['updated_by']['id'], self.user.id)

    def test_record_survives_user_deletion(self):
        vehicle = Vehicle.objects.create(
            make=self.make, name='Civic', model='2024', color='Black', engine=1500,
            created_by=self.other_user, updated_by=self.other_user,
        )
        self.other_user.delete()
        vehicle.refresh_from_db()
        self.assertIsNone(vehicle.created_by)
        res = self.client.get(f'{self.vehicle_url}{vehicle.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNone(res.data['created_by'])


class AuthenticationRequiredTests(APITestCase):
    urls = ['/api/v1/make/', '/api/v2/vehicle/']

    def test_anonymous_requests_are_rejected(self):
        for url in self.urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)
                self.assertEqual(self.client.post(url, {}, format='json').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_is_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')
        self.assertEqual(self.client.get(self.urls[0]).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_jwt_is_accepted(self):
        user = User.objects.create_user('carol@example.com', 'Str0ng-pass!')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user)['access']}")
        for url in self.urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)

    def test_deactivated_user_token_is_rejected(self):
        user = User.objects.create_user('dave@example.com', 'Str0ng-pass!')
        token = issue_tokens(user)['access']
        user.is_active = False
        user.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(self.client.get(self.urls[0]).status_code, status.HTTP_401_UNAUTHORIZED)
