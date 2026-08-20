#!/usr/bin/env bash
# Render build command — runs on every deploy.
set -o errexit

pip install -r requirements.txt
npm install
npm run build:css


# --- Compile Tailwind CSS ---
# Render's Python runtime has no Node.js, so we use Tailwind's standalone
# CLI (a self-contained binary, no npm needed) rather than `npm run build:css`.
# Pinned to v3.4.17 — the last v3 release — since this project's
# tailwind.config.js and @tailwind directives use v3 syntax; v4 changed
# both the config format and the CSS entry syntax and is not a drop-in swap.
TAILWIND_VERSION="v3.4.17"
TAILWIND_BIN="./tailwindcss-cli"

if [ ! -f "$TAILWIND_BIN" ]; then
  curl -sL -o "$TAILWIND_BIN" \
    "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-linux-x64"
  chmod +x "$TAILWIND_BIN"
fi

"$TAILWIND_BIN" -i ./static/css/input.css -o ./static/css/output.css --minify

# --- Django ---
python manage.py migrate
python manage.py seed_demo_data
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(name='admin').exists() or User.objects.create_superuser(name='admin', email='Josh@admin.com', password='User!12345')"