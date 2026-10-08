# DIVS Backend

Initial Django backend and identity/authentication foundation.

## Local setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set a secure `DJANGO_SECRET_KEY`. Environment loading is not automatic yet; export the values in your shell or configure your preferred local environment loader.
4. From the `backend/` directory, create initial migrations and apply them:

   ```bash
   python manage.py makemigrations identity
   python manage.py migrate
   python manage.py check
   python manage.py test apps.identity
   ```

SQLite is used by default for initial local development. Configure PostgreSQL environment variables for PostgreSQL development/deployment.

## Initial auth routes

- `POST /api/v1/auth/register/` — create an account using any email provider.
- `POST /api/v1/auth/token/` — obtain JWT access and refresh tokens using email/password.
- `POST /api/v1/auth/token/refresh/` — refresh an access token.
- `GET /api/v1/auth/me/` — retrieve the authenticated account.
- `GET /api/v1/auth/providers/google/` — reports whether Google provider settings exist; it does not yet complete Google sign-in.
- `GET /api/v1/auth/providers/phone/` — reports that SMS/OTP delivery is not configured.

## Not implemented yet

Email verification delivery, SMS/OTP delivery and validation, Google authorization-code/OIDC flow, password reset, account linking rules, and role/permission management remain future work. Provider readiness must not be treated as proof that a provider login flow is complete.
