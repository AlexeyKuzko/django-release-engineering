FROM python:3.13-slim
LABEL authors="Alexey Kuzko"


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    DJANGO_DEBUG=False

WORKDIR /app

# Ставим системные зависимости
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только файлы зависимостей (кэширование слоя)
COPY pyproject.toml uv.lock ./

# Генерируем requirements.txt из lock-файла
RUN pip install --no-cache-dir uv \
    && uv export --format requirements-txt > requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

# Копируем код проекта
COPY . .

# Сборка статики с production-настройками и build-time значениями обязательных env
RUN DJANGO_SECRET_KEY=docker-build-secret \
    DJANGO_ADMIN_URL=admin/ \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
    DJANGO_SECURE_SSL_REDIRECT=False \
    python manage.py collectstatic --noinput \
    && DJANGO_SECRET_KEY=docker-build-secret \
    DJANGO_ADMIN_URL=admin/ \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
    DJANGO_SECURE_SSL_REDIRECT=False \
    python manage.py compress --force

# ---- Entrypoint ----
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
