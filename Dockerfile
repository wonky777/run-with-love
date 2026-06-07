# Сборка сайта через Docker — минует nixpacks/mise на Railway и работает на любом
# Docker-хостинге (Render, Fly.io, свой VPS).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Зависимости (отдельным слоем — кешируется)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Код проекта
COPY . .

# Собираем статику (админка/DRF/Swagger) внутрь образа
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# При старте: миграции, создание админа (если заданы переменные), запуск gunicorn.
CMD python manage.py migrate --noinput && \
    (python manage.py createsuperuser --noinput || true) && \
    gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
