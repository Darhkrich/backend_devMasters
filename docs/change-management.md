# Change Management

## Required for security-sensitive changes

- Peer review on every auth, permissions, audit, or retention change
- Migration review for any model change touching security data
- Security workflow green in CI before merge
- Release notes for behavioral changes affecting sessions, login, or deletion

## Recommended approval gates

1. Developer self-review
2. Security-focused reviewer for auth/audit/session code
3. Deployment approval for production
4. Post-deploy verification using audit integrity and retention commands
