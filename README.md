# The Living Word Library — Django Project

A Django 5.x + Tailwind CSS ebook sales platform. This iteration delivers the
**Homepage** and **Authentication screens** (registration, login, email
verification, Google/Facebook social auth) on top of the book catalog,
newsletter, and contact modules.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit DJANGO_SECRET_KEY at minimum
python manage.py migrate
python manage.py seed_demo_data   # optional: sample books/settings for dev
python manage.py runserver
```

Visit `/` for the public site, `/accounts/login/` and `/accounts/signup/` for
authentication, `/admin/` to manage books and users.

For Tailwind CSS compilation: `npm install && npm run build:css` (or just run
`npm run dev` while editing styles).

## Running the tests

```bash
DJANGO_SETTINGS_MODULE=config.settings.dev python3 -m pytest tests/
python3 tests/e2e_verify.py     # browser test of the signup → verify → login flow
```

## App map

| App | Responsibility |
|---|---|
| `apps.core` | Home/About pages, `SiteSettings` singleton, `AuthorProfile` |
| `apps.books` | `Book`, `Author`, `Category`, `BuyLink` models — the CMS core; list/detail views, sitemap |
| `apps.newsletter` | `Subscriber` model, signup form/view |
| `apps.contact` | `ContactMessage` model with honeypot spam protection, contact form/view |
| `apps.accounts` | Custom `User` model (Customer/Admin roles), django-allauth adapter, signup form, profile view |

## Authentication

Authentication is handled by **django-allauth** with email as the username and
mandatory email verification:

| Feature | Implementation |
|---|---|
| Custom user model | `apps/accounts/models.py` — `User` extends `AbstractUser`, `email` is the username, `role` is `CUSTOMER`/`ADMIN` |
| Registration | `templates/account/signup.html` — name/email/password with Django password validators |
| Login | `templates/account/login.html` — email/password + "keep me signed in" |
| Social auth | `templates/account/_social_login.html` — Google and Facebook OAuth2 buttons via allauth socialaccount |
| Email verification | `templates/account/email_confirm.html` — HMAC-based confirmation links; branded verification/reset emails under `templates/account/email/` |
| Password reset | Full request → email → reset-with-key → done flow, themed to the site |
| Profile | `templates/accounts/profile.html` at `/accounts/profile/` — account type, purchases (coming next), settings links |
| Navigation | `templates/partials/_nav.html` is auth-aware: anon sees Sign in / Create account; logged-in users see their name, My account, and (admins) an Admin link |

Social login needs one-time admin setup (dev): create a
[`SocialApp`](https://docs.allauth.org/en/latest/socialaccount/configuration.html)
row for `google` and `facebook` at `/admin/socialaccount/socialapp/` with your
OAuth client ID/secret, attached to the current site. Until real credentials
exist the buttons render but OAuth flows will fail — that is expected.

In development, outgoing emails (verification, password reset) print to the
console log because `EMAIL_BACKEND` points at the console backend in
`config/settings/dev.py`. Switch to an SMTP or transactional provider in
production.

## Requirement → implementation

| Requirement | Where |
|---|---|
| Ebook upload | `Book.cover_image`, `Book.sample_excerpt` — `FileField`/`ImageField` via admin |
| Update book details / upload new books | Django admin `BookAdmin` (`apps/books/admin.py`) |
| Give discount | `Book.discount_percent` + `discount_active_until`, inline-editable on the admin list view; `Book.display_price` computes the discounted price automatically |
| Restrict books | `Book.status` (`draft` / `available` / `restricted`), inline-editable on the admin list view |
| Dual purchase path | `BuyLink` model (inline on `BookAdmin`) with "Buy PDF" / "Buy on Amazon" rendered per-book |
| Home / Books / book pages / About / Contact | `templates/core/home.html`, `templates/books/list.html`, `templates/books/detail.html`, `templates/core/about.html`, `templates/contact/contact.html` |
| Newsletter signup | `apps.newsletter` — form posts to `/newsletter/subscribe/`, on every footer and the contact page |
| Buy on Amazon | Outbound `BuyLink.url` rendered as the store-link CTA on the detail page |

## Still to do before this is production-ready

- Run `npm run build:css` (or wire Tailwind into the build) — templates reference
  `static/css/output.css`, which needs generating.
- Configure real Google/Facebook OAuth credentials as `SocialApp` rows.
- Point `EMAIL_BACKEND` at a real SMTP provider and set `DEFAULT_FROM_EMAIL`.
- Add real content: `SiteSettings`, `AuthorProfile`, and books via `/admin/`.
- Swap `USE_S3=True` in `.env` once you have R2/S3 bucket credentials, so cover
  images and sample excerpts persist across deploys.
- Add `django-recaptcha` to the contact form if spam becomes an issue beyond the
  honeypot.
- Point `DATABASE_URL` at Postgres for anything beyond local dev (SQLite is the
  default fallback).


## Current email-verification policy

Email verification is **disabled temporarily** with:

```python
ACCOUNT_EMAIL_VERIFICATION = "none"
```

This means newly registered customers and existing users can sign in without a verified `EmailAddress`. Superusers are also explicitly covered by this policy and can sign in without verification. The setting is centralized in `config/settings/base.py`; changing it to `"mandatory"` re-enables allauth's verification gate for normal authentication flows.

### Requirements to re-enable email verification

Before switching back to `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` in production, configure the following:

1. **A real email delivery service.** Set an SMTP or transactional email backend, including host, port, TLS/SSL mode, username, password, and `DEFAULT_FROM_EMAIL`. The development environment currently uses Django's console backend, which only prints messages to the terminal.
2. **A valid public site URL.** Configure the Django Sites framework (`SITE_ID = 1`) with the actual HTTPS domain. Verification links must resolve to the deployed application, not `localhost`.
3. **Production security settings.** Set a strong `DJANGO_SECRET_KEY`, enable HTTPS, configure `ALLOWED_HOSTS`, CSRF trusted origins, secure cookies, and the correct `TIME_ZONE`.
4. **Working verification templates and routes.** Keep the branded templates under `templates/account/email/` and verify that `/accounts/confirm-email/` and `/accounts/confirm-email/<key>/` are reachable.
5. **A resend and recovery path.** Users need access to the email-management/resend flow if a message expires or is lost. Test signup, resend, confirmation, expired links, duplicate addresses, and password reset end to end.
6. **Social-provider email policy.** Configure Google/Facebook `SocialApp` credentials and decide whether provider-verified emails are trusted automatically. Review `SOCIALACCOUNT_EMAIL_AUTHENTICATION` and `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT` before production use.

## Book uploads through Django admin

The `Book` admin now supports:

| Field | Purpose |
|---|---|
| `cover_image` | Required cover artwork stored under `media/covers/`. |
| `ebook_file` | Full paid PDF or EPUB stored under `media/ebooks/`. |
| `sample_excerpt` | Optional public PDF or EPUB preview stored under `media/samples/`. |
| `isbn` | Optional ISBN-10/ISBN-13 identifier. |
| `amazon_store_url` | Optional outbound Amazon listing URL. |

Open `/admin/books/book/add/`, complete the book metadata, upload the cover and ebook files, and save. The admin validates the file extensions, displays upload status in the list view, and provides preview/open links when editing an existing book. In production, the full `ebook_file` must not be exposed through a public media URL; use protected storage and signed, time-limited download views as part of the payment/fulfillment module.

The schema migration is `apps/books/migrations/0002_book_amazon_store_url_book_ebook_file_book_isbn_and_more.py`.


## Book QR codes

Each `Book` now receives an automatically generated PNG QR code whenever it is created or saved. The QR code points to the book's public detail page, for example:

```text
https://your-domain.example/books/the-qr-test-book/
```

Set `PUBLIC_SITE_URL` in `.env` to the deployed HTTPS origin before generating production codes. The local default is `http://localhost:8000`.

In Django admin, open a book to see the QR preview, the encoded target URL, and a **Download PNG** link. Changing the book slug automatically regenerates the QR image so the printed code continues to resolve to the current public detail page.

The migration is `apps/books/migrations/0003_book_qr_code.py`, and the generated files are stored under `media/qr_codes/` or the configured object-storage backend.


## Custom admin design

The Unfold admin now follows the LivingWord storefront language: parchment content surfaces, wine-colored navigation, gold focus states and rules, serif editorial headings, softened borders, and branded status badges. The sidebar groups the main library areas into Books, Orders, PayPal webhooks, Users, and Site settings.

## PayPal checkout foundation

The project now includes a `payments` app with:

- `Order` records for local buyer, book, amount, currency, PayPal order ID, capture ID, status, and raw API response.
- `PayPalWebhookEvent` records for verified webhook audit history and idempotent processing.
- REST client methods for OAuth access tokens, Orders v2 order creation, capture, and webhook signature verification.
- Authenticated create-order and capture endpoints.
- A CSRF-protected Smart Payment Buttons surface on available book detail pages when a PayPal client ID is configured.
- A CSRF-exempt webhook endpoint at `/payments/paypal/webhook/` that verifies the PayPal signature through PayPal's verification API before completing local orders.

### PayPal credentials and configuration required

| Setting | Required value | Environment |
|---|---|---|
| `PAYPAL_CLIENT_ID` | REST app client ID from the PayPal Developer Dashboard | Sandbox and live each have separate values |
| `PAYPAL_CLIENT_SECRET` | REST app client secret; keep private and never expose in templates or JavaScript | Sandbox and live each have separate values |
| `PAYPAL_WEBHOOK_ID` | ID of the webhook registered in the PayPal Developer Dashboard | One per configured app/environment |
| `PAYPAL_BASE_URL` | `https://api-m.sandbox.paypal.com` for testing or `https://api-m.paypal.com` for production | Must match the credentials |
| `PUBLIC_SITE_URL` | Public HTTPS origin used by the deployed application | Required for production return/webhook URLs |

You will also need a PayPal Business account, a sandbox buyer account for testing, and a publicly reachable HTTPS webhook URL. Register `/payments/paypal/webhook/` in the PayPal Developer Dashboard and subscribe to at least `PAYMENT.CAPTURE.COMPLETED`; the implementation also recognizes `CHECKOUT.ORDER.COMPLETED`. Before going live, test duplicate webhook delivery, failed capture, declined payment, currency/amount mismatches, and fulfillment after confirmed completion.

PayPal documentation references:

- [REST API overview](https://developer.paypal.com/api/rest)
- [Orders API integration](https://developer.paypal.com/api/rest/integration/orders-api)
- [Webhooks overview](https://developer.paypal.com/api/rest/webhooks)

The current implementation is intentionally a secure foundation. The next payment milestone is to add fulfillment: signed time-limited ebook download URLs, receipt pages, and post-purchase email delivery after a verified completed capture.


## Branding, QR display, and admin theme

The supplied LivingWord Library logo is stored at `static/images/livingword-logo.png` and is used in the storefront navigation, footer, shared authentication brand panel, and Unfold admin header. The storefront stylesheet applies responsive sizing and a blend treatment so the source image’s white background sits cleanly on the parchment design.

Book detail pages now show the generated QR code in a dedicated “Share this book” card, including its encoded public URL and a PNG download link.

The admin console uses Unfold’s built-in user-menu theme switch. The configured default is `THEME = "auto"`, allowing administrators to select Light, Dark, or system preference. The LivingWord admin stylesheet now provides matching light and dark palettes rather than forcing light surfaces.

## Email-verification environment requirements

Email verification is currently disabled with `ACCOUNT_EMAIL_VERIFICATION=none`. To enable it for production, set it to `mandatory` and provide the following values in `.env`:

```env
ACCOUNT_EMAIL_VERIFICATION=mandatory
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=The Living Word Library <noreply@example.com>
SERVER_EMAIL=noreply@example.com
EMAIL_TIMEOUT=20
SITE_DOMAIN=library.example.com
SITE_NAME=The Living Word Library
PUBLIC_SITE_URL=https://library.example.com
```

The SMTP provider must permit the sender address or domain and should have SPF, DKIM, and DMARC configured. In Django admin, the Sites record with `SITE_ID=1` must use the deployed domain rather than `localhost:8000`. The production deployment must use HTTPS, include the allauth URL routes, and retain the branded confirmation email templates. The development settings intentionally use Django’s console backend, which prints verification messages in the terminal instead of delivering them.
