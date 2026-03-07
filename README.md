# Deployment of Educational Django Application
Проект содержит автоматизированный GitLab CI/CD pipeline для развертывания Django-приложений в Yandex Cloud.

## Структура репозитория
```
├── .gitlab-ci.yml          # GitLab CI/CD pipeline
├── Dockerfile              # Dockerfile для сборки образа приложения
├── ansible/                # Ansible-роли и плейбуки
├── config/                 # Django settings
├── django_educational_demo_application/  # Django app
├── infra/                  # Terraform-модули для Yandex Cloud
└── tests/                  # Тесты
```

## О приложении
<details>
<summary>Для демонстрации работы пайплайна было разработано MVP веб-приложения "Django Educational Demo Application".</summary>

Это Learning Management System (LMS) для управления образовательными проектами и курсами.
Позволяет преподавателям создавать и управлять курсами, отслеживать прогресс работы над проектами, а студентам выполнять и сдавать задания.
### Основная функциональность
- **Курсы и зачисления** — создание учебных курсов, управление списками студентов
- **Проекты** — создание проектов со статусами (draft → in_progress → review → completed), ссылками на репозитории и развёрнутые приложения
- **Задачи** — разбиение проектов на подзадачи
- **Оценивание** — выставление оценок преподавателем, отслеживание средней оценки студента
- **Статистика** — аналитика по курсам (количество студентов, проектов, средняя оценка)
- **Аутентификация** — регистрация и вход через социальные сети (django-allauth)

### Локальный запуск
```bash
uv venv
uv sync --locked
export DATABASE_URL=postgres://<user>:<pass>@<host>:5432/<db>
uv run python manage.py migrate
uv run python manage.py runserver
```
</details>

## О пайплайне
<details>
<summary>Ключевой фокус проекта - разработка CI/CD pipeline, обеспечивающего полноценный DevOps-процесс.</summary>

### Основная функциональность
- **Автоматическая верификация кода**: security-проверки, сборка и публикация Docker-образов в GitLab Container Registry;
- **Управление инфраструктурой** на основе branch-based правил через Terraform (`apply` / `destroy` для VPC, VM, security groups);
- **Конфигурацию серверов** и деплой через Ansible веб-приложения, базы данных и мониторинга (Prometheus+Grafana);
- **Health-check с автоматическим rollback** приложения для обеспечения 100% удачного развертывания в продакшен;
- **Уведомления в Telegram**[-канал](https://t.me/dedapp_notifications) о статусе пайплайна для увеличения прозрачности процесса и повышения информативности нотификация GitLab.
</details>

## Технологии
<details>
<summary>Проект реализован с использованием следующих инструментов:</summary>

| Категория | Инструменты |
|---|---|
| Application | Django 5.2, Gunicorn, PostgreSQL, Redis |
| CI/CD | GitLab CI, GitLab Container Registry, Kaniko |
| Containerization | Docker, Docker Compose |
| IaC | Terraform (Yandex Cloud provider) |
| Configuration | Ansible |
| Testing | pytest, pytest-django, pre-commit (ruff, djLint) |
| Monitoring | Grafana, Prometheus |
</details>


## Архитектура CI/CD

### Схема пайплайна

```mermaid
flowchart LR
    subgraph Stage_Verify ["verify"]
        A1[run_linters]
        A2[run_pytest_verify]
    end

    subgraph Stage_Security ["security"]
        S1[secret_scan]
        S2[dependency_scan]
        S3[sast_semgrep]
    end

    subgraph Stage_Build ["build"]
        B1[build_image]
    end

    subgraph Stage_Test ["test"]
        T1[trivy_scan]
        T2[run_pytest_on_build]
    end

    subgraph Stage_Publish ["publish"]
        P1[publish_latest]
    end

    subgraph Stage_Prepare ["prepare_for_deploy"]
        C1[checkov]
        C2[terraform_apply<br/>]
        C3[terraform_destroy<br/>]
    end

    subgraph Stage_Deploy ["deploy"]
        D1[ansible_deploy]
        D2[health_check]
        D3[rollback]
        D4[DAST_zap]
    end

    subgraph Stage_Notify ["notify"]
        E1[notify_tg_success]
        E2[notify_tg_failure]
    end

    Stage_Verify --> Stage_Security
    S1 --> B1
    S2 --> B1
    S3 --> B1
    B1 --> T1
    B1 --> T2
    T1 --> P1
    T2 --> P1
    P1 --> C1
    C1 --> C2
    C2 -. optional .-> C3
    C2 --> D1
    D1 --> D2
    D2 --> D4
    D2 -->|success| E1
    D2 -->|failure| D3
    D3 --> E2

    style D3 fill:green
    style E1 fill:green
    style E2 fill:orange
```

> **Для наглядности диаграмма упрощена**:
> - `build_image` (Kaniko) собирает образ и сразу пушит immutable-тег `$CI_COMMIT_SHA`
> - `publish_latest` не пересобирает образ, а только проставляет теги `latest-<env>` и `previous-<env>`
> - `run_pytest_on_build` проверяет именно собранный образ: поднимает `postgres` + app-контейнер и запускает `pytest` smoke (`tests/smoke/container_image_smoke.py`)
> - `terraform_apply` для `main` запускается автоматически, для `dev/develop` — вручную
> - после успешного `terraform_apply` jobs этапа `deploy` стартуют автоматически по `needs`
> - `terraform_destroy` запускается вручную
> - `notify_tg_success` запускается после успешного `health_check`
> - `notify_tg_failure` запускается на `on_failure`


### Этапы пайплайна

| Stage | Job                       | Описание                                                                                |
|---|---------------------------|-----------------------------------------------------------------------------------------|
| `verify` | `run_linters`             | pre-commit hooks (ruff, djLint, django-upgrade)                                         |
| `verify` | `run_pytest_verify`              | набор базовых проверок с pytest в CI-окружении (с PostgreSQL service)                   |
| `security` | `secret_scan`             | Поиск секретов в репозитории (`gitleaks`)                                               |
| `security` | `dependency_scan`         | Аудит Python-зависимостей (`pip-audit`)                                                 |
| `security` | `sast_semgrep`            | SAST-проверка исходного кода (`semgrep`)                                                |
| `build` | `build_image`             | Kaniko: сборка и push immutable-образа с тегом `$CI_COMMIT_SHA`                         |
| `build` | `trivy_scan`              | Сканирование собранного образа (`HIGH`, `CRITICAL`)                                     |
| `test` | `run_pytest_on_build` | Smoke-тест собранного образа: запуск `postgres` + app-контейнера и запуск pytest-тестов |
| `publish` | `publish_latest`          | Ретегирование уже собранного образа в `latest-<env>` и `previous-<env>`                 |
| `prepare_for_deploy` | `checkov`                 | Статический анализ Terraform-конфигурации                                               |
| `prepare_for_deploy` | `terraform_apply`         | `terraform apply` + подготовка inventory (auto в `main`, manual в `dev/develop`)        |
| `prepare_for_deploy` | `terraform_destroy`       | Ручной `terraform destroy`                                                              |
| `deploy` | `ansible_deploy`          | Деплой через Ansible + Docker Compose                                                   |
| `deploy` | `health_check`            | Проверка HTTPS `/health` и `/`                                                          |
| `deploy` | `rollback`                | Откат к `previous-<env>` при провале health_check                                       |
| `deploy` | `DAST_zap`                | DAST baseline-скан после успешного health-check                                         |
| `notify` | `notify_tg_success` | Уведомляет в Telegram об успешном завершении пайплайна                                  |
| `notify` | `notify_tg_failure` | Уведомляет в Telegram о провале с указанием конкретной job                              |

**Правила запуска:**
- Автоматически на push запускаются `verify` → `security` → `build` → `test`
- Для веток `main` (`prod`) и `dev`/`develop` (`dev`) дополнительно запускается `publish_latest`
- В `main` `terraform_apply` запускается автоматически
- В `dev`/`develop` `terraform_apply` доступен как manual job
- `terraform_destroy` остается manual job
- После успешного `terraform_apply` автоматически запускаются jobs этапа `deploy`
- `notify_tg_success` отправляется после успешного `health_check` (для `main` и `dev`/`develop`)
- `notify_tg_failure` отправляется на любой сбой (`on_failure`) в `main` и `dev`/`develop`
- `rollback` и `notify_tg_failure` запускаются при ошибке

### Build vs Publish

`build_image` и `publish_latest` разделены по ответственности:
- `build_image` (Kaniko) собирает Docker-образ из `Dockerfile` и публикует immutable-тег `$CI_COMMIT_SHA`
- `publish_latest` работает уже с опубликованным образом в реестре: переносит `latest-<env>` в `previous-<env>` и ставит `latest-<env>` на текущий SHA

Итог: шаги не дублируют друг друга. Первый создаёт артефакт сборки, второй продвигает его как «текущий» для окружения и подготавливает данные для rollback.



## Реализованный функционал

### Полностью реализовано ✅

- **CI Pipeline:** auto-часть `verify → security → build → test → publish`; в `main` деплойный контур автоматический, в `dev/develop` `terraform_apply`/`terraform_destroy` запускаются вручную; после `terraform_apply` выполняются `deploy → notify`
- **Terraform IaC:** VPC, subnets (public/private), NAT Gateway, security groups, VM (app/db/monitoring), опциональная DNS-зона
- **Ansible деплой:** idempotent-роли для app, db, monitoring; авто-определение docker-compose команды
- **Image Tagging:** commit SHA + `latest-dev/latest-prod` + `previous-dev/previous-prod` (для rollback)
- **Post-build smoke test:** запуск собранного Docker-образа вместе с PostgreSQL и `pytest`-проверка доступности `/health` и `/`
- **Health-check:** HTTPS проверка `/health` и главной страницы с fallback на IP
- **Rollback:** автоматический откат к `previous-<env>` при провале health_check
- **Terraform destroy:** ручное удаление инфраструктуры
- **S3 Backend:** состояние Terraform в Yandex Object Storage (`dev/terraform.tfstate`, `prod/terraform.tfstate`)
- **Изоляция окружений:** отдельные VPC/subnets/NAT для dev и prod

### Ограничения ⚠️

- **Rollback:** хранится только один предыдущий тег (`previous-<env>`); первый деплой откатывать некуда
- **DNS:** при `MANAGE_DNS=true` требуется делегирование NS на регистраторе для ACME challenge
- **Health-check:** fallback на HTTP/IP при некоторых HTTPS-сбоях; strict-fail только для DNS-ошибок (`curl rc=6`)

## Тестирование

**10 тест-файлов:**
- `django_educational_demo_application/users/tests/` (5 файлов: admin, forms, models, urls, views)
- `tests/test_health_endpoint.py`
- `tests/test_home_page.py`
- `tests/test_merge_production_dotenvs_in_dotenv.py`
- `tests/smoke/container_image_smoke.py`

**Особенности:**
- Тесты используют PostgreSQL (не совместимы с SQLite из-за sequence в миграциях `contrib/sites`)
- CI запускает pytest с PostgreSQL service
- Пост-сборочный smoke stage запускает отдельный `pytest` против собранного Docker-образа



Production-переменные: `DJANGO_SECRET_KEY`, `DJANGO_ADMIN_URL`, `DJANGO_ALLOWED_HOSTS` и др.

## Архитектура инфраструктуры

```mermaid
flowchart TB

subgraph YC["Yandex Cloud"]

subgraph GITLAB["Managed Service for GitLab"]
GL["GitLab CI/CD"]
REG["GitLab Container Registry"]
GL --> REG
end

subgraph VPC["VPC Network (<env>)"]

subgraph PUBLIC["Public Subnet"]
APP["App VM<br/>(Django + Caddy)<br/>:443 :80"]
MON["Monitoring VM<br/>(Grafana + Prometheus)<br/>:3000 :9090"]
end

subgraph PRIVATE["Private Subnet"]
DB["DB VM<br/>(PostgreSQL)<br/>:5432"]
end

end

SG["Security Groups<br/>(app_sg, db_sg, mon_sg)"]

APP --- SG
DB --- SG
MON --- SG

NAT["NAT Gateway"]

VPC --- NAT

GL -->|Terraform apply/destroy| VPC
GL -->|Ansible deploy + health check| APP
APP -->|image pull| REG

end
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
