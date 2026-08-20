from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import Order, PayPalWebhookEvent


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("paypal_order_id", "book", "user", "amount_display", "status_badge", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("paypal_order_id", "paypal_capture_id", "payer_email", "user__email", "book__title")
    readonly_fields = ("created_at", "updated_at", "completed_at", "raw_response")
    list_select_related = ("book", "user")

    @admin.display(description="Amount", ordering="amount")
    def amount_display(self, obj):
        return f"{obj.currency} {obj.amount}"

    @admin.display(description="Status")
    def status_badge(self, obj):
        color = {
            Order.Status.COMPLETED: "#2f6b43",
            Order.Status.FAILED: "#9a2e2e",
            Order.Status.APPROVED: "#9a6a17",
        }.get(obj.status, "#5a1b1e")
        return format_html(
            '<span style="display:inline-block;padding:.25rem .55rem;border-radius:999px;background:{};color:#fff;font-size:.75rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;">{}</span>',
            color,
            obj.get_status_display(),
        )


@admin.register(PayPalWebhookEvent)
class PayPalWebhookEventAdmin(ModelAdmin):
    list_display = ("event_type", "paypal_event_id", "verification_status", "received_at", "processed_at")
    list_filter = ("event_type", "verification_status", "received_at")
    search_fields = ("paypal_event_id", "event_type")
    readonly_fields = ("paypal_event_id", "event_type", "verification_status", "payload", "processing_error", "received_at", "processed_at")
