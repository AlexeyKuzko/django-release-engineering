# Django Release Engineering

Release-engineering case study for a Django learning-management application: a staged CI/CD design, reproducible Python dependencies, container checks, Terraform and Ansible delivery, health checks, rollback, and monitoring.

## Overview

This repository combines a Django application with the delivery system built around it. GitHub is the canonical source of truth. The retained GitLab CI/CD definition is historical case-study evidence, not an active dependency, and this repository does not claim a hosted demo or live infrastructure.

The application models courses, projects, tasks, students, and enrollment workflows. The engineering focus is the path from a reviewed commit to a tested image and an explicitly enabled deployment.

## Delivery Flow

The pipeline definition in [`.gitlab-ci.yml`](.gitlab-ci.yml) separates verification, security, build, runtime testing, image promotion, infrastructure preparation, deployment, and notification:

```text
verify -> security -> build -> test -> publish -> prepare_for_deploy -> deploy -> notify
```

- `run_linters` and `run_pytest_verify` gate the security stage.
- Gitleaks scans full Git history and is blocking.
- Bandit, pip-audit, Trivy, and Checkov surface unresolved findings as advisory jobs.
- Kaniko builds one immutable image per commit; a Docker-in-Docker job tests the built image with PostgreSQL.
- Image promotion, Terraform, Ansible, health checks, DAST, rollback, and deployment notifications are separated into explicit jobs.
- `DEPLOY_ENABLED` defaults to `false`. Deployment rules require the exact value `true`, a supported branch, and a non-documentation change.

## Architecture

The delivery design has four boundaries:

1. **Application:** Django, PostgreSQL, Redis integration, authentication, course/project workflows, and `/health`.
2. **Artifact:** a Python 3.13 container built from the locked runtime dependency set in [`uv.lock`](uv.lock).
3. **Infrastructure:** Terraform models Yandex Cloud networking, compute, security groups, DNS options, and remote state; Ansible configures application, database, and monitoring hosts.
4. **Operations:** Caddy fronts the application; Prometheus and Grafana provide the monitoring layer; health checks and a single previous image tag support rollback.

The database is placed on a private subnet. The application and monitoring hosts receive the connectivity needed by the delivery design, while security-group rules remain explicit in [`infra/`](infra/).

## Evidence Map

| Capability | Primary evidence | What to inspect |
| --- | --- | --- |
| CI/CD orchestration | [`.gitlab-ci.yml`](.gitlab-ci.yml) | stages, `needs`, advisory versus blocking checks, deploy rules |
| Reproducible Python environment | [`pyproject.toml`](pyproject.toml), [`uv.lock`](uv.lock) | exact Python and package pins, dev tooling |
| Container build and runtime test | [`Dockerfile`](Dockerfile), [`tests/smoke/`](tests/smoke/) | locked production export, image-level health and homepage checks |
| Django behavior | [`django_educational_demo_application/`](django_educational_demo_application/), [`tests/`](tests/) | domain models, views, user flows, health endpoint |
| Infrastructure as code | [`infra/`](infra/) | network, compute, DNS, security, variables, outputs |
| Configuration management | [`ansible/`](ansible/) | common, app, database, and monitoring roles |
| Rollback and health | [`.gitlab-ci.yml`](.gitlab-ci.yml) | previous-image promotion, health gates, rollback job |
| Provenance | [`NOTICE`](NOTICE), [`CONTRIBUTORS.txt`](CONTRIBUTORS.txt) | template attribution and contributor acknowledgement |

## Trade-offs

- The GitLab pipeline is retained because it is material engineering evidence; GitHub remains canonical, so no GitLab availability or parity is assumed.
- Security tools remain visible but advisory where their baselines are unresolved. This preserves signal without presenting known debt as a passing gate.
- Terraform and Ansible demonstrate a complete cloud delivery path, but the Yandex Cloud implementation is less portable than a provider-neutral example.
- Rollback uses one `previous-<environment>` image tag. It is simple to operate but provides only one-generation recovery and cannot help on a first deployment.
- Deployment automation is deliberately inert by default. An operator must opt in with `DEPLOY_ENABLED=true`, and documentation-only changes do not satisfy deploy rules.

## Testing and Security

The test suite covers users, forms, URLs, views, project/course behavior, production dotenv assembly, the homepage, and the health endpoint. Image smoke tests exercise the built container against PostgreSQL. A fully provisioned environment is expected to collect 49 Django tests; that is a validation target, not a claim that every checkout has executed them.

Security controls represented in the pipeline include:

- blocking full-history Gitleaks scanning;
- advisory Bandit source analysis and pip-audit dependency analysis;
- advisory Trivy image scanning and Checkov Terraform analysis;
- locked dependency synchronization and a locked, production-only Docker export;
- an ignored Git history, environment directory, virtual environments, Terraform, and Ansible content in the Docker build context;
- explicit deployment opt-in and change-based deployment rules.

Three historical assigned values were removed from all reachable history during repository preparation and must be treated as compromised. This repository does not claim that external copies, credentials, or resources were rotated or decommissioned.

## Rollback

Before promoting a new image, the pipeline records the current `latest-<environment>` image as `previous-<environment>`. If the post-deployment health check fails, the rollback job redeploys that previous tag through the Ansible application role.

Rollback is conditional on a previous image existing, covers one generation, and has not been represented here as proof of a live production recovery. Infrastructure destruction remains a separate manual operation and is not part of routine validation.

## Verified Results

The local hardening checkpoint recorded the following non-remote results:

- the rewritten repository preserves five distinct branch histories and zero tags;
- all 187 reachable commits retained author, committer, timestamp, message, and parent relationships while affected tree and commit IDs changed;
- the three approved historical values have zero occurrences in reachable blobs and commit diffs;
- Gitleaks 8.30.1 reported zero findings across rewritten history;
- `git fsck --full --strict` and `uv lock --check` completed successfully;
- configuration acceptance checks cover CI dependencies, deploy gating, Docker hardening, documentation structure, and contributor attribution.

Application execution, dependency auditing, Terraform validation, Ansible linting, and image builds require the tools and services listed below. A result is not implied when those prerequisites are absent.

## Run and Validate

Create the locked environment and a local PostgreSQL database:

```bash
uv sync --locked
createdb django_educational_demo_application
export DATABASE_URL=postgresql:///django_educational_demo_application
uv run python manage.py migrate
```

Run the application and its principal checks:

```bash
uv run python manage.py check
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run djlint django_educational_demo_application/templates --check
uv run python manage.py runserver
```

Validate generated dependency and infrastructure inputs without deploying:

```bash
uv lock --check
uv export --locked --no-dev --format requirements-txt --output-file /tmp/requirements.txt
docker build -t django-release-engineering:local .
terraform -chdir=infra init -backend=false
terraform -chdir=infra validate
ansible-lint ansible/
```

Do not run Terraform apply/destroy or Ansible deployment against an account you do not control. Supply deployment credentials only through a protected external secret store; do not commit them.

## Prerequisites

- Python `3.13.x`
- `uv` `0.11.28` for the documented lock/export workflow
- PostgreSQL 15-compatible service for Django tests
- Docker with a running daemon for image validation
- Terraform 1.6-compatible CLI for infrastructure validation
- Ansible and `ansible-lint` for configuration validation
- cloud credentials, SSH material, DNS ownership, and a container registry only for an explicitly authorized deployment

## Repository Layout

```text
.
├── config/                                  # Django settings, URLs, WSGI
├── django_educational_demo_application/     # application code, templates, tests
├── tests/                                   # health, homepage, dotenv, image smoke tests
├── infra/                                   # Terraform infrastructure
├── ansible/                                 # roles, inventory, templates
├── Dockerfile                               # locked production image build
├── pyproject.toml                           # project and tool configuration
├── uv.lock                                  # reproducible dependency resolution
└── .gitlab-ci.yml                           # historical CI/CD case-study definition
```

## Limitations

- There is no supported live-demo URL and no claim that cloud resources are currently running.
- GitLab is not an active dependency or source of truth; the retained pipeline definition was not validated against a live GitLab instance during this hardening pass.
- Dependency-vulnerability status remains an advisory residual: the preparation environment had neither package-index DNS nor a cached `pip-audit`, so dependencies and `uv.lock` were not changed and no clean audit is claimed.
- The full Django suite requires both the locked packages and PostgreSQL; environments missing either prerequisite cannot substantiate the 49-test target.
- Bandit, pip-audit, Trivy, and Checkov remain advisory until their baselines are reviewed and resolved.
- The infrastructure is provider-specific, requires external credentials, and must not be treated as a turnkey production platform.
- External rotation or decommissioning of previously exposed values could not be verified from GitHub and is not claimed.

## Contribution

### My Contribution

This was a team diploma project. Git attribution on `main` shows my authored changes across Terraform, Ansible, the Django application, automated tests, documentation, and most of the GitLab CI/CD pipeline. Matvei Sukhikh contributed security-pipeline changes. This describes commit attribution, not exclusive ownership.

### Acknowledgements

Matvei Sukhikh contributed security-pipeline changes. See [`CONTRIBUTORS.txt`](CONTRIBUTORS.txt) for the contributor list. Contributions should be proposed through a focused branch with tests and documentation appropriate to the change; deployment must remain disabled unless an authorized operator explicitly enables it.

## Provenance and License

The project originated from the cookiecutter-django template. Template provenance and its BSD 3-Clause notice are preserved in [`NOTICE`](NOTICE).

Project-specific work is available under the [MIT License](LICENSE). Contributor attribution is recorded in [`CONTRIBUTORS.txt`](CONTRIBUTORS.txt); the contribution statement above describes Git attribution and does not claim exclusive ownership.
