# Incident Response

## Severity model

- `SEV1`: confirmed breach, active compromise, or sensitive data exposure
- `SEV2`: attempted compromise or significant auth/control failure
- `SEV3`: suspicious activity with limited impact

## Initial response checklist

1. Identify affected users, systems, and time window.
2. Preserve logs and run `python manage.py verify_audit_integrity`.
3. Revoke impacted sessions and rotate exposed credentials.
4. Review blocked IPs, security events, and recent admin access.
5. Document timeline, impact, containment, and follow-up actions.

## Evidence sources

- `AuditLog`
- `SecurityEvent`
- `DeviceSession`
- `BlockedIP`
- CI security workflow results

## Post-incident requirements

- Root-cause analysis
- Corrective action plan
- Change review for the remediation
- Customer/internal communication where required
