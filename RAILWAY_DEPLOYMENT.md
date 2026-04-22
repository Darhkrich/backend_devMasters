## Railway Deployment Notes

This backend uses cookie-based JWT authentication. When the frontend and backend run on different origins, login can appear to succeed and then immediately bounce back to the login page if the browser does not send the backend auth cookies back on `/api/v1/auth/me/`.

### Required backend environment variables

For a Railway frontend at `https://your-frontend.up.railway.app`, set:

```env
APP_ENV=production
DEBUG=False
FRONTEND_URL=https://your-frontend.up.railway.app
CORS_ALLOWED_ORIGINS=https://your-frontend.up.railway.app
CSRF_TRUSTED_ORIGINS=https://your-frontend.up.railway.app
AUTH_COOKIE_SAMESITE=None
AUTH_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SAMESITE=None
CSRF_COOKIE_SECURE=True
```

Leave `AUTH_COOKIE_DOMAIN`, `SESSION_COOKIE_DOMAIN`, and `CSRF_COOKIE_DOMAIN` blank unless you are intentionally sharing cookies across subdomains on the same parent domain.

### Required frontend environment variable

Point the frontend at the deployed backend API:

```env
NEXT_PUBLIC_BOEM_API_BASE_URL=https://your-backend.up.railway.app/api/v1
```

### Email configuration

If you want registration, verification, and password-reset emails to work in Railway, also set:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-smtp-username
EMAIL_HOST_PASSWORD=your-smtp-password-or-app-password
DEFAULT_FROM_EMAIL=your-from-address
```

Verification links are built from `FRONTEND_URL`, so make sure that value points to your public frontend domain, not localhost.

### Deployment behavior

The Docker image sets `APP_ENV=production` by default and runs:

1. `python manage.py migrate`
2. `python manage.py ensure_superuser`
3. `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

If you change either Railway URL or add a custom domain later, update `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` to the exact new frontend origin before testing login again.
