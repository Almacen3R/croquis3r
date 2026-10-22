from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings


@override_settings(THREER_PRICING_ENABLED=False)
class AuthenticatedTestCase(TestCase):
    """Existing calculation/view fixtures run as an administrator; privacy has separate tests."""
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_superuser('test_admin', 'admin@example.invalid', None)
        self.client.force_login(self.user)
