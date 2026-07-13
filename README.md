# Django Release Engineering

Release-engineering case study for a Django learning-management application: CI/CD design, locked Python dependencies, container checks, Terraform and Ansible delivery, health checks, rollback, and monitoring.

## Overview

GitHub is the canonical source. The retained GitLab pipeline is case-study evidence, not an active dependency; this repository does not claim a hosted demo or live infrastructure. The Django application models courses, projects, tasks, students, and enrolment workflows. Its focus is the path from reviewed commit to tested image and explicitly enabled deployment.

## Delivery and architecture

```text
verify -> security -> build -> test -> publish -> prepare_for_deploy -> deploy -> notify
```

- Linters and pytest gate the security stage; full-history Gitleaks is blocking.
- Bandit, pip-audit, Trivy, and Checkov remain advisory while their baselines are unresolved.
- Kaniko builds an immutable image; Docker-in-Docker smoke tests it with PostgreSQL.
- Promotion, Terraform, Ansible, health checks, rollback, DAST, and notifications are explicit jobs.
- `DEPLOY_ENABLED=false` by default. Deployment requires the exact value `true`, a supported branch, and a non-documentation change.

The design separates four boundaries: **application** (Django, PostgreSQL, Redis, `/health`), **artifact** (Python 3.13 image from [`uv.lock`](uv.lock)), **infrastructure** ([`infra/`](infra/) Terraform and [`ansible/`](ansible/) roles), and **operations** (Caddy, Prometheus, Grafana, health checks, and one previous image tag for rollback).

## Evidence map

| Capability | Inspect |
| --- | --- |
| CI/CD and deployment rules | [`.gitlab-ci.yml`](.gitlab-ci.yml) |
| Locked Python environment | [`pyproject.toml`](pyproject.toml), [`uv.lock`](uv.lock) |
| Image build and smoke tests | [`Dockerfile`](Dockerfile), [`tests/smoke/`](tests/smoke/) |
| Django behavior | [`django_educational_demo_application/`](django_educational_demo_application/), [`tests/`](tests/) |
| Infrastructure and configuration | [`infra/`](infra/), [`ansible/`](ansible/) |
| Attribution and provenance | [`CONTRIBUTORS.txt`](CONTRIBUTORS.txt), [`NOTICE`](NOTICE) |

## Validation and limits

The test suite covers users, forms, URLs, views, course/project behavior, dotenv assembly, homepage, and health endpoint; image smoke tests use PostgreSQL. A fully provisioned environment is expected to collect 49 Django tests, but this is a target rather than a claim for every checkout.

The hardening checkpoint recorded five retained branch histories, no tags, 187 preserved commits, zero occurrences of three removed historical values, zero Gitleaks 8.30.1 findings, successful `git fsck --full --strict`, successful `uv lock --check`, and configuration acceptance checks. Those removed values must be treated as compromised; rotation or decommissioning of external copies and resources is not claimed.

Rollback copies `latest-<environment>` to `previous-<environment>` before promotion and redeploys that tag after a failed health check. It covers one generation only and is not proof of a live production recovery. Terraform, Ansible, cloud credentials, live GitLab, dependency audits, and image builds require the local tools and services below; advisory findings do not become passing gates merely because a scanner is unavailable.

## Run and validate

Prerequisites: Python `3.13.x`, `uv` `0.11.28`, PostgreSQL 15-compatible service, Docker, Terraform 1.6-compatible CLI, Ansible with `ansible-lint`; cloud credentials and registry access are needed only for an explicitly authorised deployment.

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

Do not run Terraform apply/destroy or Ansible deployment against an account you do not control. Keep deployment credentials in a protected external secret store.

## Contribution and provenance

### My Contribution

This was a team diploma project. Git attribution on `main` shows my authored changes across Terraform, Ansible, the Django application, automated tests, documentation, and most of the GitLab CI/CD pipeline. Matvei Sukhikh contributed security-pipeline changes. This describes commit attribution, not exclusive ownership.

Matvei Sukhikh is listed in [`CONTRIBUTORS.txt`](CONTRIBUTORS.txt). The project originated from cookiecutter-django; its BSD 3-Clause notice is preserved in [`NOTICE`](NOTICE). Project-specific work is available under the [MIT License](LICENSE).
