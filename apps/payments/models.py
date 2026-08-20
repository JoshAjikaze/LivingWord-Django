from decimal import Decimal

from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        APPROVED = "approved", "Approved"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    book = models.ForeignKey("books.Book", on_delete=models.PROTECT, related_name="orders")
    paypal_order_id = models.CharField(max_length=80, unique=True, blank=True)
    paypal_capture_id = models.CharField(max_length=80, blank=True, default="")
    payer_email = models.EmailField(blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        reference = self.paypal_order_id or f"local-{self.pk}"
        return f"{reference} — {self.book.title}"


class PayPalWebhookEvent(models.Model):
    paypal_event_id = models.CharField(max_length=120, unique=True)
    event_type = models.CharField(max_length=160)
    verification_status = models.CharField(max_length=32, default="PENDING")
    payload = models.JSONField(default=dict)
    processing_error = models.TextField(blank=True, default="")
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.event_type} — {self.paypal_event_id}"
