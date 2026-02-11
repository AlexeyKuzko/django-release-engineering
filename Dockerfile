FROM python:3.13-slim
LABEL authors="kuzko_alexey"

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --locked

COPY . .

ENV DJANGO_SETTINGS_MODULE=config.settings.production

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
