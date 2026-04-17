# Backup and Retention

## Backup expectations

- Database backups should be encrypted at rest and in transit.
- Test restore procedures on a fixed schedule.
- Store backup retention separately from application retention windows.

## Application retention controls

- `AUDIT_LOG_RETENTION_DAYS`
- `SECURITY_EVENT_RETENTION_DAYS`
- `LOGIN_HISTORY_RETENTION_DAYS`
- `DEVICE_SESSION_RETENTION_DAYS`

Run:

```bash
python manage.py enforce_retention_policies --dry-run
python manage.py enforce_retention_policies
```

before production scheduling to confirm deletion scope.
