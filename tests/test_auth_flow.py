"""Functional auth flow tests for the public site and temporary auth policy."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

User = get_user_model()


@override_settings(ACCOUNT_EMAIL_VERIFICATION="none")
class AuthFlowTests(TestCase):
    def test_homepage_loads(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Explore the Books")

    def test_nav_shows_auth_ctas_for_anonymous(self):
        resp = self.client.get("/")
        self.assertContains(resp, "/accounts/signup/")
        self.assertContains(resp, "/accounts/login/")

    def test_signup_creates_customer(self):
        resp = self.client.post(
            "/accounts/signup/",
            {"name": "Test Reader", "email": "reader@example.com", "password1": "SecureP@ss1", "password2": "SecureP@ss1"},
        )
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(email="reader@example.com")
        self.assertEqual(user.role, "customer")
        self.assertEqual(user.name, "Test Reader")
        self.assertFalse(user.is_staff)

    def test_duplicate_email_rejected(self):
        User.objects.create_user(email="dup@example.com", password="SecureP@ss1", name="Dup")
        resp = self.client.post(
            "/accounts/signup/",
            {"name": "Another", "email": "dup@example.com", "password1": "SecureP@ss1", "password2": "SecureP@ss1"},
        )
        # allauth marks the email as taken but still logs the user in as unverified
        self.assertEqual(User.objects.filter(email="dup@example.com").count(), 1)

    def test_unverified_customer_can_login_while_verification_is_disabled(self):
        User.objects.create_user(email="unverified@example.com", password="SecureP@ss1", name="Unverified")
        resp = self.client.post(
            "/accounts/login/",
            {"login": "unverified@example.com", "password": "SecureP@ss1"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/accounts/profile/")

    def test_superuser_can_login_without_email_verification(self):
        User.objects.create_superuser(
            email="root@example.com", password="SecureP@ss1", name="Root User"
        )
        resp = self.client.post(
            "/accounts/login/",
            {"login": "root@example.com", "password": "SecureP@ss1"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/accounts/profile/")

    def test_password_must_match_validators(self):
        resp = self.client.post(
            "/accounts/signup/",
            {"name": "Weak", "email": "weak@example.com", "password1": "12345678", "password2": "12345678"},
        )
        self.assertEqual(resp.status_code, 200)  # stays on form with errors

    def test_login_page_loads(self):
        resp = self.client.get("/accounts/login/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Sign in")

    def _seed_social_apps(self):
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site

        site = Site.objects.get(id=settings.SITE_ID)
        for provider in ("google", "facebook"):
            if not SocialApp.objects.filter(provider=provider).exists():
                app = SocialApp.objects.create(
                    provider=provider,
                    name=provider.capitalize(),
                    client_id=f"dev-{provider}-id",
                    secret=f"dev-{provider}-secret",
                )
                app.sites.add(site)

    def test_social_login_panel_renders_when_providers_exist(self):
        self._seed_social_apps()
        resp = self.client.get("/accounts/login/")
        self.assertContains(resp, "Continue with Google")
        self.assertContains(resp, "Continue with Facebook")

    def test_profile_page_requires_login(self):
        resp = self.client.get("/accounts/profile/")
        self.assertEqual(resp.status_code, 302)

    def test_authenticated_nav_changes(self):
        user = User.objects.create_user(email="nav@example.com", password="SecureP@ss1", name="Nav")
        self.client.force_login(user)
        resp = self.client.get("/")
        self.assertNotContains(resp, "Create account")
        self.assertContains(resp, "My account")

    def test_admin_role_sees_admin_link(self):
        user = User.objects.create_superuser(email="admin@example.com", password="SecureP@ss1", name="Admin")
        self.client.force_login(user)
        resp = self.client.get("/")
        self.assertContains(resp, "/admin/")
