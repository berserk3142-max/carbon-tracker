#!/usr/bin/env bash
set -e

export PORT="${PORT:-7860}"

mkdir -p media staticfiles

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_data

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout "${WEB_TIMEOUT:-120}"
