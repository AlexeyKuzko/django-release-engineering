FROM python:3.13-slim
LABEL authors="Alexey Kuzko"

ENV DJANGO_SETTINGS_MODULE=config.settings.build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.build
ENV DJANGO_DEBUG=False

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

# Сборка статики
RUN python manage.py collectstatic --noinput \
    && python manage.py compress

# ---- Entrypoint ----
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
