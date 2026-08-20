from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.social.models import SocialAccount, SocialDelivery, SocialPost
from apps.social.services import SocialPublishError, enqueue_post, validate_post


class SocialPublishingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(email="social-admin@example.com", password="SecureP@ss1", name="Social Admin")
        self.account = SocialAccount.objects.create(
            platform=SocialAccount.Platform.X,
            name="LivingWord X",
            external_id="x-user-1",
            connected_by=self.user,
        )
        self.account.access_token = "secret-token"
        self.account.save(update_fields=["access_token_ciphertext", "updated_at"])

    def test_social_token_is_encrypted_at_rest(self):
        account = SocialAccount.objects.get(pk=self.account.pk)
        self.assertEqual(account.access_token, "secret-token")
        self.assertNotIn("secret-token", account.access_token_ciphertext)

    def test_x_character_limit_is_validated(self):
        post = SocialPost.objects.create(body="x" * 281, created_by=self.user)
        post.accounts.add(self.account)
        with self.assertRaises(SocialPublishError):
            validate_post(post, self.account)

    def test_enqueue_creates_one_delivery_per_active_account(self):
        post = SocialPost.objects.create(body="A new LivingWord release.", created_by=self.user)
        post.accounts.add(self.account)
        enqueue_post(post)
        post.refresh_from_db()
        self.assertEqual(post.status, SocialPost.Status.QUEUED)
        self.assertEqual(SocialDelivery.objects.filter(post=post, account=self.account).count(), 1)

    def test_social_account_admin_exposes_connection_buttons(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("admin:social_socialaccount_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Connect Facebook")
        self.assertContains(response, "Connect Instagram")
        self.assertContains(response, "Connect Threads")
        self.assertContains(response, "Connect YouTube")
        self.assertContains(response, "Connect X")

    def test_oauth_start_requires_provider_client_id(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("social:oauth_start", kwargs={"platform": "x"}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin:index"))
