# Architecture Boundaries

## App boundaries

- `apps.users`
  - Identity, account lifecycle, profile management, device sessions, and user-facing auth orchestration.
- `apps.security`
  - Threat detection, alerting, rate controls, security analytics, and post-auth security processing.
- `apps.audit`
  - Immutable audit logging, integrity verification, and access review reporting.
- `apps.core`
  - Shared infrastructure: caching, events, task dispatch, versioning, checks, and cross-cutting middleware.

## Integration rules

- User-facing flows may publish domain events through `apps.core.events`.
- Background work should be queued through `apps.core.tasks`, not called ad hoc from view code.
- Read-heavy analytics endpoints should use cached service/query functions rather than embedding ORM-heavy logic in views.
- Cross-app imports should prefer service/event interfaces over reaching directly into unrelated view modules.

## Current background strategy

- `TASK_QUEUE_MODE=sync`
  - Safe default for local/dev and deterministic test behavior.
- `TASK_QUEUE_MODE=thread`
  - Lightweight async execution for non-blocking background work without introducing a full broker yet.

If this system grows further, the next upgrade path should be a real worker/broker pair rather than expanding threaded execution.
