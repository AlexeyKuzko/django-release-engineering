FROM python:3.13-slim
LABEL authors="Alexey Kuzko"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production
ENV DJANGO_DEBUG=False

WORKDIR /app

# Системные зависимости
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только файлы зависимостей (кэширование слоя)
COPY pyproject.toml uv.lock ./

# Устанавливаем uv и зависимости В СИСТЕМНЫЙ Python
RUN pip install uv \
    && uv sync --locked

# Копируем код проекта
COPY . .

# Сборка статики
RUN python manage.py collectstatic --noinput
RUN python manage.py compress

# ---- Entrypoint ----
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
