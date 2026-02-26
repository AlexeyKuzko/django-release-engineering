# Deployment of Educational Django Application

Автоматизированный GitLab CI/CD pipeline для развертывания Django-приложения в Yandex Cloud.

## Назначение

CI/CD pipeline обеспечивает:
- автоматическую сборку и публикацию Docker-образов в GitLab Container Registry;
- развёртывание инфраструктуры через Terraform (VPC, VM, security groups);
- конфигурацию серверов и деплой через Ansible;
- health-check развернутого приложения;
- автоматический откат при неудачной проверке;
- уведомления в Telegram о результатах деплоя.

## Технологии

| Категория | Инструменты |
|---|---|
| Application | Django 5.2, Gunicorn, PostgreSQL, Redis |
| Containerization | Docker, Docker Compose |
| CI/CD | GitLab CI, GitLab Container Registry, Kaniko |
| IaC | Terraform (Yandex Cloud provider) |
| Configuration | Ansible |
| Testing | pytest, pytest-django, pre-commit (ruff, djLint) |
| Monitoring | Grafana, Prometheus |

## Структура репозитория

```
├── .gitlab-ci.yml          # GitLab CI/CD pipeline
├── Dockerfile              # Образ приложения
├── infra/                  # Terraform-модули для Yandex Cloud
├── ansible/                # Ansible-роли и плейбуки
├── config/                 # Django settings
├── django_educational_demo_application/  # Django app
└── tests/                  # Тесты
```

## Архитектура CI/CD

### Схема пайплайна

```mermaid
flowchart LR
    subgraph Stage_Test ["test"]
        A1[run_linters]
        A2[run_pytest]
    end

    subgraph Stage_Build ["build"]
        B1[build_image]
        B2[publish_latest]
    end

    subgraph Stage_Infra ["infra"]
        C1[terraform_apply]
        C2[terraform_destroy]
    end

    subgraph Stage_Deploy ["deploy"]
        D1[ansible_deploy]
        D2[health_check]
        D3[rollback]
    end

    subgraph Stage_Notify ["notify"]
        E1[notify_telegram_success]
        E2[notify_telegram_failure]
    end

    A1 --> B1
    A2 --> B1
    B1 --> B2
    B1 --> C1
    B2 --> D1
    C1 -. manual .-> C2
    C1 --> D1
    D1 --> D2
    D2 -->|success| E1
    D2 -->|failure| D3
    D3 --> E2

    style D3 fill:green
    style E1 fill:green
    style E2 fill:orange
```

> **Для наглядности диаграмма упрощена**:
> - `publish_latest` и `terraform_apply` выполняются параллельно после `build_image`
> - `ansible_deploy` требует артефакты от `terraform_apply` и `publish_latest`
> - `notify_telegram_success` запускается `on_success` - когда не осталось pending/failed jobs (не только после `health_check`)
> - `notify_telegram_failure` запускается на `on_failure` при любой ошибке (не только после `rollback`)


### Этапы пайплайна

| Stage | Job | Описание |
|---|---|---|
| `test` | `run_linters` | pre-commit hooks (ruff, djLint, django-upgrade) |
| `test` | `run_pytest` | pytest с PostgreSQL service |
| `build` | `build_image` | Kaniko: сборка и push с тегом `$CI_COMMIT_SHA` |
| `build` | `publish_latest` | Тегирование `latest-dev`/`latest-prod` и `previous-dev`/`previous-prod` |
| `infra` | `terraform_apply` | Создание инфраструктуры в Yandex Cloud |
| `infra` | `terraform_destroy` | Ручное удаление инфраструктуры |
| `deploy` | `ansible_deploy` | Деплой через Ansible + Docker Compose |
| `deploy` | `health_check` | Проверка HTTPS `/health` и `/` |
| `deploy` | `rollback` | Откат к `previous-<env>` при провале health_check |
| `notify` | `notify_telegram_*` | Уведомления в Telegram |

**Правила запуска:**
- Ветки `main` → окружение `prod`, `dev`/`develop` → окружение `dev`
- `terraform_destroy` запускается вручную
- `rollback` и `notify_telegram_failure` запускаются при ошибке



## Реализованный функционал

### Полностью реализовано ✅

- **CI Pipeline:** test → build → (publish \|\| terraform) → deploy → health_check → rollback/notify
- **Terraform IaC:** VPC, subnets (public/private), NAT Gateway, security groups, VM (app/db/monitoring), опциональная DNS-зона
- **Ansible деплой:** idempotent-роли для app, db, monitoring; авто-определение docker-compose команды
- **Image Tagging:** commit SHA + `latest-dev/latest-prod` + `previous-dev/previous-prod` (для rollback)
- **Health-check:** HTTPS проверка `/health` и главной страницы с fallback на IP
- **Rollback:** автоматический откат к `previous-<env>` при провале health_check
- **Terraform destroy:** ручное удаление инфраструктуры
- **S3 Backend:** состояние Terraform в Yandex Object Storage (`dev/terraform.tfstate`, `prod/terraform.tfstate`)
- **Изоляция окружений:** отдельные VPC/subnets/NAT для dev и prod

### Ограничения ⚠️

- **Rollback:** хранится только один предыдущий тег (`previous-<env>`); первый деплой откатывать некуда
- **DNS:** при `MANAGE_DNS=true` требуется делегирование NS на регистраторе для ACME challenge
- **Health-check:** fallback на HTTP/IP при некоторых HTTPS-сбоях; strict-fail только для DNS-ошибок (`curl rc=6`)
- **Секреты:** требуют настройки в GitLab CI/CD Variables (masked/protected)

## Тестирование

**9 тест-файлов:**
- `django_educational_demo_application/users/tests/` (5 файлов: admin, forms, models, urls, views)
- `tests/test_health_endpoint.py`
- `tests/test_home_page.py`
- `tests/test_merge_production_dotenvs_in_dotenv.py`

**Особенности:**
- Тесты используют PostgreSQL (не совместимы с SQLite из-за sequence в миграциях `contrib/sites`)
- CI запускает pytest с PostgreSQL service

## Локальный запуск

```bash
uv venv
uv sync --locked
export DATABASE_URL=postgres://<user>:<pass>@<host>:5432/<db>
uv run python manage.py migrate
uv run python manage.py runserver
```

Production-переменные: `DJANGO_SECRET_KEY`, `DJANGO_ADMIN_URL`, `DJANGO_ALLOWED_HOSTS` и др.

## Архитектура инфраструктуры

```
┌─────────────────────────────────────────────────────────────────┐
│                      Yandex Cloud                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   App VM     │  │    DB VM     │  │ Monitoring VM│          │
│  │  (Django +   │  │ (PostgreSQL) │  │ (Grafana +   │          │
│  │   Caddy)     │  │              │  │  Prometheus) │          │
│  │  :443, :80   │  │   :5432      │  │  :3000, :9090│          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
│              ┌────────────┴────────────┐                        │
│              │     Security Groups     │                        │
│              │  (app_sg, db_sg, mon_sg)│                        │
│              └────────────┬────────────┘                        │
│                           │                                     │
│         ┌─────────────────┴─────────────────┐                   │
│         │       VPC Network (<env>)         │                   │
│         │  ┌──────────┐  ┌──────────┐      │                   │
│         │  │  public  │  │ private  │      │                   │
│         │  │  subnet  │  │  subnet  │      │                   │
│         │  │          │  │          │      │                   │
│         │  │ App VM   │  │  DB VM   │      │                   │
│         │  │ Mon VM   │  │          │      │                   │
│         │  └──────────┘  └──────────┘      │                   │
│         └─────────────────┬─────────────────┘                   │
│                           │                                     │
│                    ┌──────┴──────┐                              │
│                    │ NAT Gateway │                              │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │ HTTPS
                            │
                    ┌───────┴───────┐
                    │   GitLab CI   │
                    │   Pipeline    │
                    │               │
                    │ test→         │
                    │ build→(publish│
                    │ ||terraform)→ │
                    │ deploy→check  │
                    └───────────────┘
```

## Конфигурация

### Переменные Terraform

| Переменная | Описание | Пример |
|---|---|---|
| `app_domain` | FQDN приложения | `app.example.com` |
| `manage_dns` | Управлять DNS-зоной через Terraform | `true`/`false` |
| `dns_zone` | Базовая DNS-зона | `example.com` |
| `dns_zone_resource_name` | Имя ресурса DNS-зоны | `diploma-zone-dev` |
| `environment` | Имя окружения | `dev`/`prod` |

### Переменные GitLab CI/CD

| Переменная | Описание | Scope |
|---|---|---|
| `APP_DOMAIN` | Домен приложения (обязательная) | environment |
| `MANAGE_DNS` | Управление DNS (`true`/`false`) | environment |
| `DNS_ZONE` | DNS-зона | environment |
| `DNS_ZONE_RESOURCE_NAME` | Имя зоны в YC DNS | environment |
| `DJANGO_SECRET_KEY` | Секрет Django | environment, masked |
| `DJANGO_ADMIN_URL` | URL админки | environment |
| `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Параметры БД | environment, masked |
| `TLS_ACME_EMAIL` | Email для Let's Encrypt | environment |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Уведомления | masked |
| `YC_SERVICE_ACCOUNT_KEY` | Ключ сервисного аккаунта | masked |
| `SSH_PUBLIC_KEY`, `SSH_PRIVATE_KEY` | SSH ключи | masked |
| `YC_STORAGE_ACCESS_KEY`, `YC_STORAGE_SECRET_KEY` | S3 backend | masked |

**Определение окружения в зависимости от Git branch:**
- `main` → `prod`
- `dev`/`develop` → `dev`

### DNS делегирование

При `MANAGE_DNS=true` Terraform создаёт публичную DNS-зону и выводит:
- `dns_zone_id`
- `dns_zone_name`
- `dns_delegation_name_servers` (NS-серверы)

Требуется делегирование NS у регистратора для работы ACME challenge (Let's Encrypt).
