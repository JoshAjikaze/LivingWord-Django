#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install production dependencies inside Render's environment
pip install -r requirements.txt

cp .env.example .env

# Compile static assets and apply migrations
python manage.py collectstatic --no-input
python manage.py migrate

npm install
npm run build:css