web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && (python manage.py createsuperuser --noinput || true) && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
