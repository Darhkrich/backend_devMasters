# API Versioning and Deprecation Policy

## Current versioning model

- URL version prefix: `/api/v1/...`
- Runtime version detection: `apps.core.versioning.ProjectPathVersioning`
- Response header: `X-API-Version`

## Policy

- New breaking changes should ship in a new version prefix.
- Existing versions should remain stable during their support window.
- Deprecated versions should return:
  - `Deprecation: true`
  - `Sunset: <date>`
  - `Link: <policy-url>; rel="deprecation"`

## Discovery

- Clients can call:

```bash
GET /api/v1/core/versions/
```

to see the default, supported, and deprecated versions.
