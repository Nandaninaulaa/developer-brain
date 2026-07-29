#!/bin/sh
set -e

cd /app/backend

echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

PORT="${PORT:-8000}"
echo "==> Starting gunicorn on 0.0.0.0:${PORT}..."
exec gunicorn devbrain_project.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --timeout 120
