# Deploying to Render.com

This project is already configured for Render: `render.yaml` (Blueprint), `build.sh`, and `config/settings/prod.py` are all in place and have been verified locally (build commands run clean, gunicorn boots and serves real requests, HTTPS redirect behaves correctly behind Render's proxy).

## Option A — Blueprint deploy (recommended, one click)

1. Push this repo to GitHub/GitLab/Bitbucket, including `render.yaml`, `build.sh`, and `requirements.txt`.
2. In the Render Dashboard, go to **Blueprints** → **New Blueprint Instance**.
3. Select this repository and click **Connect**.
4. Give the blueprint a name and click **Apply**.

Render reads `render.yaml` and creates both the **web service** and a **free Postgres database** automatically, wiring `DATABASE_URL` between them. `DJANGO_SECRET_KEY` is auto-generated. The app will be live at `<name>.onrender.com` once the build finishes.

## Option B — Manual setup

1. **Database first**: Render Dashboard → **New** → **PostgreSQL**. Copy the **Internal Database URL** once it's created.
2. **New Web Service** → connect the repo.
3. Runtime: `Python 3`. Set:

   | Field | Value |
   |---|---|
   | Build Command | `./build.sh` |
   | Start Command | `gunicorn config.wsgi:application` |

4. Under **Environment**, add:

   | Key | Value |
   |---|---|
   | `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
   | `DATABASE_URL` | the Internal Database URL from step 1 |
   | `DJANGO_SECRET_KEY` | click **Generate** |
   | `WEB_CONCURRENCY` | `4` |
   | `PYTHON_VERSION` | `3.12.4` |
   | `USE_S3` | `False` (see note below) |

5. Save — Render builds and deploys.

## After first deploy

Create an admin user via the Render **Shell** tab (or `render ssh <service-name>` with the CLI):

```bash
python manage.py createsuperuser
python manage.py seed_demo_data   # optional — populates the 6 placeholder books
```

## Media files — read this before uploading real book covers

Render's web service filesystem is **ephemeral** — anything written to disk (i.e. `MEDIA_ROOT`, where cover images and sample excerpts land) is wiped on every deploy and every restart. With `USE_S3=False`, uploaded covers will disappear the next time you push a change.

Before uploading real content, set up object storage:

1. Create a Cloudflare R2 bucket (or AWS S3).
2. Add these environment variables in Render:

   | Key | Value |
   |---|---|
   | `USE_S3` | `True` |
   | `AWS_ACCESS_KEY_ID` | from your bucket |
   | `AWS_SECRET_ACCESS_KEY` | from your bucket |
   | `AWS_STORAGE_BUCKET_NAME` | your bucket name |
   | `AWS_S3_ENDPOINT_URL` | R2 endpoint (omit entirely for AWS S3) |

   These map directly to the `USE_S3` block already in `config/settings/base.py` — no code changes needed, just the env vars.
3. Redeploy (env var changes trigger a redeploy automatically).

Until this is set up, treat the deployed site as a **preview environment** — fine for reviewing design/copy with the client, not for real book uploads.

## Free tier behavior to expect

- The free web service **spins down after 15 minutes of inactivity**; the next request triggers a 30–60 second cold start. Fine for a staging/review link, not ideal as the final production URL if the client cares about first-load speed. Upgrade to a paid instance type to remove this.
- The free Postgres database **expires after 90 days** on Render's free tier — fine for development, plan to upgrade before this becomes the real production database.

## Custom domain

Once ready to point the client's real domain at it: Render Dashboard → your web service → **Settings** → **Custom Domains** → add the domain, then create the CNAME/A record Render gives you at your DNS provider. Add the domain to `ALLOWED_HOSTS` in `config/settings/prod.py` (it's currently only auto-populated for the `.onrender.com` hostname via `RENDER_EXTERNAL_HOSTNAME`).
