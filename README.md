# Django Educational Demo Application

This is a demo project that demonstrates the use of Django, Docker, and GitLab CI/CD for a simple web application deployment.

License: MIT

## Deployment scheme

- PostgreSQL: `systemd`
- Django/Gunicorn/Nginx: `docker-compose`
- Monitoring: `docker-compose`
- Terraform: только создание VM + network
- Ansible: конфигурация и деплой

### 1. Общая логика пайплайна

CI pipeline:

`Build -> Test -> Publish -> Terraform Apply -> Ansible Deploy -> Smoke Test -> (Rollback при ошибке)`

Разделение ответственности:
- GitLab CI: оркестрация
- Terraform: создание инфраструктуры
- Ansible: конфигурация и доставка
- Docker Compose: запуск сервисов на App VM и Monitoring VM

### 2. Инфраструктура (Terraform)

Создаваемые ресурсы.

Сеть:
- VPC
- 2 подсети:
  - `public-subnet` (App VM + Monitoring VM)
  - `private-subnet` (DB VM)
- Security Groups:
  - App: `80`, `443`, `22`
  - DB: `5432` (только от App)
  - Monitoring: `3000`, `9090` (ограничить IP)

VM 1 (App VM):
- Docker
- Docker Compose
- Nginx (можно контейнером)
- Django (container)
- Gunicorn (container)

Порты:
- `80`/`443` наружу
- `8000` только локально

VM 2 (DB VM):
- PostgreSQL (`systemd`, не контейнер)
- Volume для данных
- Firewall: доступ только с App VM

Почему не контейнер:
- корректнее для production
- лучше контроль персистентности

VM 3 (Monitoring VM):
- Docker
- Prometheus
- Grafana
- `node_exporter` на всех VM

### 3. Terraform структура

```text
infra/
├── main.tf
├── variables.tf
├── outputs.tf
├── network.tf
├── app_vm.tf
├── db_vm.tf
└── monitoring_vm.tf
```

State:
- S3 backend

CI:

```bash
terraform init
terraform validate
terraform plan
terraform apply -auto-approve
```

### 4. Ansible структура

```text
ansible/
├── inventory.tpl
├── site.yml
└── roles/
    ├── common/
    ├── app/
    ├── db/
    └── monitoring/
```

Роль `common`:
- users
- docker
- firewall
- `node_exporter`

Роль `app`:
- `docker login` в registry
- pull image
- template `docker-compose.yml`
- `docker compose up -d`
- healthcheck

Роль `db`:
- install postgres
- create db
- create user
- настроить `pg_hba.conf`
- restart

Роль `monitoring`:
- `docker compose` для Prometheus + Grafana
- provision dashboards

### 5. Docker Compose

Используется только как runtime-слой
- не как механизм деплоя
- Ansible управляет Compose

То есть:

`Ansible -> кладет docker-compose.yml -> docker compose up -d`


### 6. Принципиально важные моменты

1. Rollback

Rollback это откат Docker image tag

Ansible:

```text
previous_tag = stored in file or CI variable
docker compose down
docker compose up -d with previous image
```

2. Smoke test после деплоя

После Ansible:

```bash
curl http://app/health
```

Если fail, запускается rollback job.

3. Секреты
- DB password: GitLab CI variables
- не хранятся в Terraform
- передаются через Ansible vars

## Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    uv run coverage run -m pytest
    uv run coverage html
    uv run open htmlcov/index.html

#### Running tests with pytest

    uv run pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html#using-webpack-or-gulp).
