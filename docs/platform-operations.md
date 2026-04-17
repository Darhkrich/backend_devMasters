# Platform Operations

## Settings

- `config.settings.dev` is the local development profile.
- `config.settings.test` is the isolated CI and pytest profile.
- `config.settings.staging` enables secure cookies, Redis-backed channels/cache, and the durable worker mode.
- `config.settings.prod` extends staging and keeps production-only validation strict.

## Background Processing

- Runtime task dispatch is controlled by `TASK_QUEUE_MODE`.
- `sync` executes inline and is reserved for local/test usage.
- `worker` stores jobs durably in `core_taskjob` and expects one or more `python manage.py run_task_worker` processes.
- User emails, suspicious login checks, and security alerts already flow through this worker path.

## Observability

- Every API response now includes `X-Request-ID` and `X-Trace-ID`.
- Liveness: `GET /api/v1/core/health/live/`
- Readiness: `GET /api/v1/core/health/ready/`
- Metrics: `GET /api/v1/core/metrics/`
- Protect metrics with `METRICS_AUTH_TOKEN` or a staff-authenticated caller.

## Delivery

- `.github/workflows/ci.yml` runs formatting, linting, type checks, Django checks, tests, migration drift checks, and a container build.
- `.github/workflows/security.yml` remains the security-focused workflow for Bandit, Semgrep, and dependency auditing.
- `.github/workflows/deploy.yml` builds and publishes an image to GHCR and can trigger staged deployments through `DEPLOY_WEBHOOK_URL`.

## Production Topology

- `docker-compose.prod.yml` defines `db`, `redis`, `migrate`, `web`, and `worker`.
- `web` serves the ASGI application through Daphne.
- `worker` runs the durable task processor.
- `redis` backs Channels and the shared cache in staging/production.
