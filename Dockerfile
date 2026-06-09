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

# Стартовый скрипт исполняемый
RUN chmod +x /app/start.sh

EXPOSE 8000

# Старт: миграции, опц. суперюзер, затем gunicorn (логи в stdout, exec => PID 1).
# Скрипт логирует каждый шаг — в Deploy Logs видно, дошли ли до gunicorn и порт.
CMD ["/app/start.sh"]
