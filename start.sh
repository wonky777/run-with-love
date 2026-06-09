#!/usr/bin/env bash
set -u
echo "[start] migrate..."
python manage.py migrate --noinput
echo "[start] createsuperuser (optional)..."
python manage.py createsuperuser --noinput 2>/dev/null || true
echo "[start] launching gunicorn on port ${PORT:-8000}"
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
