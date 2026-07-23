# The Living Word Library — Django Project

A working starting repo: 4 apps, models, admin CMS, and the homepage templates already wired together and verified (`manage.py check` passes, migrations generate cleanly).

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit DJANGO_SECRET_KEY at minimum
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `/admin/` to manage books, and `/` for the public site.

For Tailwind CSS compilation, see the earlier `package.json` / `tailwind.config.js` / `static/css/input.css` — copy those into this project root and run `npm install && npm run build:css`.

## App map

| App | Responsibility |
|---|---|
| `apps.core` | Home/About pages, `SiteSettings` singleton (editable homepage copy), `AuthorProfile` |
| `apps.books` | `Book`, `BuyLink` models — the CMS core; list/detail views, sitemap |
| `apps.newsletter` | `Subscriber` model, signup form/view |
| `apps.contact` | `ContactMessage` model with honeypot spam protection, contact form/view |

## Requirement → implementation

| Requirement | Where |
|---|---|
| Ebook upload | `Book.cover_image`, `Book.sample_excerpt` — `FileField`/`ImageField` via admin |
| Update book details / upload new books | Django admin `BookAdmin` (`apps/books/admin.py`) |
| Give discount | `Book.discount_percent` + `discount_active_until`, inline-editable on the admin list view; `Book.display_price` computes the discounted price automatically |
| Restrict books | `Book.status` (`draft` / `available` / `restricted`), inline-editable on the admin list view |
| Home / Books / book pages / About / Contact | `templates/core/home.html`, `templates/books/list.html`, `templates/books/detail.html`, `templates/core/about.html`, `templates/contact/contact.html` |
| Buy links (Amazon etc.) | `BuyLink` model, inline on `BookAdmin`, rendered per-book on the detail page |
| Newsletter signup | `apps.newsletter` — form posts to `/newsletter/subscribe/`, included on every page footer and the contact page |

## Still to do before this is production-ready

- Run `npm run build:css` (or wire Tailwind into the build) — templates currently reference `static/css/output.css`, which needs generating.
- Add real content: at least one `SiteSettings` row, one `AuthorProfile`, and the 6 `Book` records via `/admin/`.
- Swap `USE_S3=True` in `.env` once you have R2/S3 bucket credentials, so cover images and sample excerpts persist across deploys.
- Add `django-recaptcha` to the contact form if spam becomes an issue beyond the honeypot.
- Point `DATABASE_URL` at Postgres for anything beyond local dev (SQLite is the default fallback).
