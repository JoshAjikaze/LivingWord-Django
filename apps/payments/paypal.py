from __future__ import annotations

from typing import Any

import requests
from django.conf import settings


class PayPalAPIError(RuntimeError):
    """Raised when PayPal rejects an API request or credentials are incomplete."""


class PayPalClient:
    def __init__(self):
        self.base_url = settings.PAYPAL_BASE_URL.rstrip("/")
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET

    @property
    def configured(self):
        return bool(self.client_id and self.client_secret)

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        if not self.configured:
            raise PayPalAPIError("PayPal credentials are not configured.")
        response = requests.request(
            method,
            f"{self.base_url}{path}",
            timeout=20,
            **kwargs,
        )
        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text}
        if not response.ok:
            raise PayPalAPIError(f"PayPal returned HTTP {response.status_code}: {data}")
        return data

    def access_token(self) -> str:
        if not self.configured:
            raise PayPalAPIError("PayPal credentials are not configured.")
        response = requests.post(
            f"{self.base_url}/v1/oauth2/token",
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"},
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            timeout=20,
        )
        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text}
        if not response.ok or "access_token" not in data:
            raise PayPalAPIError(f"PayPal token request failed: {data}")
        return data["access_token"]

    def _authorized_headers(self, request_id: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token()}",
        }
        if request_id:
            headers["PayPal-Request-Id"] = request_id
        return headers

    def create_order(self, *, amount: str, currency: str, book_title: str, reference_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v2/checkout/orders",
            headers=self._authorized_headers(request_id=f"livingword-create-{reference_id}"),
            json={
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": reference_id,
                        "description": book_title[:127],
                        "custom_id": reference_id,
                        "amount": {"currency_code": currency, "value": amount},
                    }
                ],
                "application_context": {
                    "brand_name": "The Living Word Library",
                    "user_action": "PAY_NOW",
                    "shipping_preference": "NO_SHIPPING",
                },
            },
        )

    def capture_order(self, paypal_order_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v2/checkout/orders/{paypal_order_id}/capture",
            headers=self._authorized_headers(request_id=f"livingword-capture-{paypal_order_id}"),
            json={},
        )

    def verify_webhook(self, *, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
        verification_payload = {
            "auth_algo": headers.get("PAYPAL-AUTH-ALGO", ""),
            "cert_url": headers.get("PAYPAL-CERT-URL", ""),
            " transmission_id": headers.get("PAYPAL-TRANSMISSION-ID", ""),
            "transmission_id": headers.get("PAYPAL-TRANSMISSION-ID", ""),
            "transmission_sig": headers.get("PAYPAL-TRANSMISSION-SIG", ""),
            "transmission_time": headers.get("PAYPAL-TRANSMISSION-TIME", ""),
            "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            "webhook_event": payload,
        }
        verification_payload.pop(" transmission_id", None)
        return self._request(
            "POST",
            "/v1/notifications/verify-webhook-signature",
            headers=self._authorized_headers(),
            json=verification_payload,
        )
