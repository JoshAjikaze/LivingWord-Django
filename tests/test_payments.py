import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.books.models import Book
from apps.payments.models import Order, PayPalWebhookEvent


@override_settings(PAYPAL_CLIENT_ID="", PAYPAL_CLIENT_SECRET="", PAYPAL_WEBHOOK_ID="")
class PayPalConfigurationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="buyer@example.com",
            password="SecureP@ss1",
            name="Book Buyer",
        )
        self.book = Book.objects.create(
            title="Payment Test Book",
            slug="payment-test-book",
            short_description="A payment test book.",
            description="Payment test description.",
            status=Book.Status.AVAILABLE,
            price="12.00",
        )
        self.client.force_login(self.user)

    def test_create_order_returns_safe_configuration_error(self):
        response = self.client.post(reverse("payments:paypal_create", args=[self.book.slug]))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(Order.objects.get().status, Order.Status.FAILED)
        self.assertIn("PayPal credentials", response.json()["error"])

    def test_webhook_does_not_process_without_paypal_credentials(self):
        payload = {"id": "WH-configuration-test", "event_type": "PAYMENT.CAPTURE.COMPLETED"}
        response = self.client.post(
            reverse("payments:paypal_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        event = PayPalWebhookEvent.objects.get(paypal_event_id="WH-configuration-test")
        self.assertEqual(event.verification_status, "FAILED")
