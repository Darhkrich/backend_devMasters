# Security and Compliance Foundations

## Startup validation and secrets

- Environment parsing is centralized in `config/env.py`.
- Staging and production now require `SECRET_KEY`, `DB_PASSWORD`, and `AUDIT_LOG_SIGNING_KEY`.
- Use `.env.example` as the template for non-secret configuration.
- Rotate any credentials that were ever committed into `.env`.

## Token and session hardening

- `DeviceSession` now stores `refresh_token_hash` instead of persisting plaintext refresh tokens.
- Session records track trust, expiry, rotation, and revocation metadata.
- Refresh token rotation is handled by `CustomTokenRefreshView`.
- Password changes and password resets revoke active device sessions.

## Audit integrity and reviews

- `AuditLog` entries are chained with `previous_hash` and `entry_hash`.
- Audit logs are immutable once written.
- Retention is controlled by `AUDIT_LOG_RETENTION_DAYS`.
- Verify integrity with:

```bash
python manage.py verify_audit_integrity
```

- Generate an access review report with:

```bash
python manage.py admin_access_review --days 30
```

## Retention and deletion workflows

- Enforce configured retention windows with:

```bash
python manage.py enforce_retention_policies --dry-run
python manage.py enforce_retention_policies
```

- Anonymize a user for deletion/privacy workflows with:

```bash
python manage.py anonymize_user --email user@example.com
python manage.py anonymize_user --user-id 123
```

## Continuous security review

- `.github/workflows/security.yml` runs:
  - Django checks
  - Bandit SAST
  - `pip-audit`
  - Semgrep
- Schedule a recurring manual penetration review and threat-model review at least quarterly.
