# Django Release Engineering

Дипломный проект DevOps-магистратуры: release engineering для учебной Django LMS

Сохранённый GitLab pipeline служит примером реализации; demo-стенд и облачная инфраструктура остановлены.

## Обзор

Главный фокус — путь от проверенного коммита до протестированного образа и явно разрешённого deployment.
CI/CD, зафиксированные Python-зависимости, контейнерные проверки, доставка через Terraform и Ansible, health checks, rollback и мониторинг.

## Доставка и архитектура

```text
verify -> security -> build -> test -> publish -> prepare_for_deploy -> deploy -> notify
```

- Linters и pytest блокируют переход к security stage; Gitleaks проверяет всю историю и является блокирующим.
- Bandit, pip-audit, Trivy и Checkov остаются advisory-проверками до устранения их baseline findings.
- Kaniko собирает неизменяемый образ; smoke-тесты Docker-in-Docker проверяют его с PostgreSQL.
- Promotion, Terraform, Ansible, health checks, rollback, DAST и уведомления разделены на самостоятельные jobs.
- По умолчанию задано `DEPLOY_ENABLED=false`. Deployment требует значения `true`, поддерживаемой ветки и изменения за пределами документации.

Архитектура разделена на четыре слоя: **приложение** (Django, PostgreSQL, Redis, `/health`), **артефакт** (образ Python 3.13 из [`uv.lock`](uv.lock)), **инфраструктура** (Terraform в [`infra/`](infra/) и роли [`ansible/`](ansible/)) и **operations** (Caddy, Prometheus, Grafana, health checks и предыдущий образ для rollback).

## Карта реализации

| Возможность                      | Где смотреть                                                                                       |
|----------------------------------|----------------------------------------------------------------------------------------------------|
| CI/CD и правила deployment       | [`.gitlab-ci.yml`](.gitlab-ci.yml)                                                                 |
| Зафиксированное Python-окружение | [`pyproject.toml`](pyproject.toml), [`uv.lock`](uv.lock)                                           |
| Сборка образа и smoke-тесты      | [`Dockerfile`](Dockerfile), [`tests/smoke/`](tests/smoke/)                                         |
| Поведение Django                 | [`django_educational_demo_application/`](django_educational_demo_application/), [`tests/`](tests/) |
| Инфраструктура и конфигурация    | [`infra/`](infra/), [`ansible/`](ansible/)                                                         |
| Авторство и происхождение        | [`CONTRIBUTORS.txt`](CONTRIBUTORS.txt), [`NOTICE`](NOTICE)                                         |

## Запуск и проверка

Требования: Python `3.13.x`, `uv` `0.11.28`, PostgreSQL 15-совместимый сервис, Docker, Terraform 1.6-совместимый CLI, Ansible и `ansible-lint`. Cloud credentials и registry access нужны только для явно разрешённого deployment.

```bash
uv sync --locked
createdb django_educational_demo_application
export DATABASE_URL=postgresql:///django_educational_demo_application
uv run python manage.py migrate
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run djlint django_educational_demo_application/templates --check
```

```bash
uv lock --check
uv export --locked --no-dev --format requirements-txt --output-file /tmp/requirements.txt
docker build -t django-release-engineering:local .
terraform -chdir=infra init -backend=false
terraform -chdir=infra validate
ansible-lint ansible/
```

## Вклад и происхождение

Это был командный дипломный проект, Matvei Sukhikh внёс изменения в security pipeline.

Проект основан на cookiecutter-django; уведомление BSD 3-Clause сохранено в [`NOTICE`](NOTICE). 

Собственная часть проекта распространяется по [MIT License](LICENSE).

