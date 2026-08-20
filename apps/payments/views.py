import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.books.models import Book

from .models import Order, PayPalWebhookEvent
from .paypal import PayPalAPIError, PayPalClient


def _paypal_headers(request):
    return {
        "PAYPAL-AUTH-ALGO": request.headers.get("PAYPAL-AUTH-ALGO", ""),
        "PAYPAL-CERT-URL": request.headers.get("PAYPAL-CERT-URL", ""),
        "PAYPAL-TRANSMISSION-ID": request.headers.get("PAYPAL-TRANSMISSION-ID", ""),
        "PAYPAL-TRANSMISSION-SIG": request.headers.get("PAYPAL-TRANSMISSION-SIG", ""),
        "PAYPAL-TRANSMISSION-TIME": request.headers.get("PAYPAL-TRANSMISSION-TIME", ""),
    }


@login_required
@require_POST
def create_paypal_order(request, slug):
    book = get_object_or_404(Book, slug=slug, status=Book.Status.AVAILABLE)
    order = Order.objects.create(
        user=request.user,
        book=book,
        amount=book.display_price,
        currency="USD",
    )
    try:
        paypal_order = PayPalClient().create_order(
            amount=f"{order.amount:.2f}",
            currency=order.currency,
            book_title=book.title,
            reference_id=str(order.pk),
        )
    except PayPalAPIError as exc:
        order.status = Order.Status.FAILED
        order.raw_response = {"error": str(exc)}
        order.save(update_fields=["status", "raw_response", "updated_at"])
        return JsonResponse({"error": str(exc)}, status=503)

    order.paypal_order_id = paypal_order.get("id", "")
    order.raw_response = paypal_order
    order.status = Order.Status.CREATED
    order.save(update_fields=["paypal_order_id", "raw_response", "status", "updated_at"])
    return JsonResponse({"order_id": order.paypal_order_id, "local_order_id": order.pk})


@login_required
@require_POST
def capture_paypal_order(request, paypal_order_id):
    order = get_object_or_404(Order, paypal_order_id=paypal_order_id, user=request.user)
    try:
        captured = PayPalClient().capture_order(paypal_order_id)
    except PayPalAPIError as exc:
        order.status = Order.Status.FAILED
        order.raw_response = {"error": str(exc)}
        order.save(update_fields=["status", "raw_response", "updated_at"])
        return JsonResponse({"error": str(exc)}, status=503)

    capture = (captured.get("purchase_units") or [{}])[0].get("payments", {}).get("captures", [{}])[0]
    order.raw_response = captured
    order.paypal_capture_id = capture.get("id", "")
    order.status = Order.Status.COMPLETED if captured.get("status") == "COMPLETED" else Order.Status.APPROVED
    if order.status == Order.Status.COMPLETED:
        order.completed_at = timezone.now()
    order.save(update_fields=["raw_response", "paypal_capture_id", "status", "completed_at", "updated_at"])
    return JsonResponse({"status": order.status, "order_id": order.paypal_order_id})


@csrf_exempt
@require_POST
def paypal_webhook(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    event_id = payload.get("id")
    event_type = payload.get("event_type", "")
    if not event_id:
        return JsonResponse({"error": "Missing PayPal event ID."}, status=400)

    if PayPalWebhookEvent.objects.filter(paypal_event_id=event_id, processed_at__isnull=False).exists():
        return JsonResponse({"status": "already_processed"})

    event, _ = PayPalWebhookEvent.objects.get_or_create(
        paypal_event_id=event_id,
        defaults={"event_type": event_type, "payload": payload},
    )
    try:
        verification = PayPalClient().verify_webhook(headers=_paypal_headers(request), payload=payload)
    except PayPalAPIError as exc:
        event.verification_status = "FAILED"
        event.processing_error = str(exc)
        event.save(update_fields=["verification_status", "processing_error"])
        return JsonResponse({"error": "Webhook verification unavailable."}, status=503)

    if verification.get("verification_status") != "SUCCESS":
        event.verification_status = "INVALID"
        event.save(update_fields=["verification_status"])
        return JsonResponse({"error": "Invalid PayPal webhook signature."}, status=400)

    event.verification_status = "SUCCESS"
    resource = payload.get("resource") or {}
    paypal_order_id = (
        resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
        or resource.get("custom_id")
        or resource.get("id")
    )
    order = Order.objects.filter(paypal_order_id=paypal_order_id).first()
    if order and event_type in {"CHECKOUT.ORDER.COMPLETED", "PAYMENT.CAPTURE.COMPLETED"}:
        order.status = Order.Status.COMPLETED
        order.completed_at = timezone.now()
        order.raw_response = {"webhook": payload}
        order.paypal_capture_id = resource.get("id", order.paypal_capture_id)
        order.save(update_fields=["status", "completed_at", "raw_response", "paypal_capture_id", "updated_at"])
    event.processed_at = timezone.now()
    event.save(update_fields=["verification_status", "processed_at"])
    return JsonResponse({"status": "received"})
