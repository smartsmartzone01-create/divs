from django.test import TestCase, override_settings
from django.urls import path
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.identity.models import Account
from apps.profiles.models import DriverProfile
from apps.registrations.models import DriverRegistration
from common.views import RoleProtectedAPIView


class DriverOnlyTestView(RoleProtectedAPIView):
    required_profile_type = "driver"

    def get(self, request):
        return Response({"allowed": True})


urlpatterns = [path("role-protected-test/", DriverOnlyTestView.as_view())]


@override_settings(ROOT_URLCONF=__name__)
class SharedRoleProtectedViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.account = Account.objects.create_user(
            email="driver-api@example.com",
            phone_number="+255700000022",
            password="StrongPassword123!",
        )
        self.url = "/role-protected-test/"

    def test_endpoint_requires_active_driver_profile(self):
        self.client.force_authenticate(user=self.account)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

        registration = DriverRegistration.objects.create(
            account=self.account,
            first_name="Amani",
            middle_name="",
            last_name="Juma",
            nationality="Tanzanian",
            region="Dar es Salaam",
            district="Kinondoni",
            current_residential_address="Mikocheni",
            driving_experience="1_to_3_years",
        )
        DriverProfile.objects.create(registration=registration)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["allowed"])
