# PayPal integration research notes

PayPal official documentation reviewed on 2026-08-18:

- Orders API integration: https://developer.paypal.com/api/rest/integration/orders-api
- REST API overview and app access tokens: https://developer.paypal.com/api/rest
- Webhooks overview and verification approaches: https://developer.paypal.com/api/rest/webhooks

Implementation implications: use PayPal REST API Orders v2 for checkout order creation and capture; obtain OAuth access tokens using the app client ID and client secret; validate incoming webhook authenticity using PayPal's webhook verification mechanism and the configured webhook ID rather than trusting an unverified payload. Separate sandbox and live credentials and endpoints.
