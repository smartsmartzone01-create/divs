# DIVS Backend

Django backend with a shared identity/authentication foundation and a separate role-registration module. Driver registration is implemented; client and operations-admin registrations, profile modules, verification workflows, and workspace access gates remain future steps.

## Local setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set a secure `DJANGO_SECRET_KEY`. Environment loading is not automatic yet; export values in your shell or configure a local environment loader.
4. From the `backend/` directory, create and apply initial migrations, then run checks and tests:

   ```bash
   python manage.py makemigrations identity registrations
   python manage.py migrate
   python manage.py check
   python manage.py test apps.identity apps.registrations
   ```

SQLite and local-memory caching are used by default for local development. Configure PostgreSQL and a shared Redis cache for deployment. Rate limiting based on local-memory cache is not shared between multiple application workers.

## Shared authentication routes

- `POST /api/v1/auth/token/` — sign in using `identifier` (verified email or verified phone number) and `password`.
- `POST /api/v1/registrations/driver/` — create the authenticated account's driver registration.
- `GET /api/v1/registrations/driver/` — retrieve that account's driver registration.
- `PATCH /api/v1/registrations/driver/` — update that account's driver registration.
- `POST /api/v1/auth/token/refresh/` — refresh a token while its tracked device session remains active.
- `GET /api/v1/auth/me/` — retrieve the authenticated account.
- `POST /api/v1/auth/verification/request/` — request an email or phone verification code.
- `POST /api/v1/auth/verification/confirm/` — verify a six-digit code.
- `POST /api/v1/auth/providers/google/sign-in/` — validate a Google ID token and sign in only when that Google subject is already linked to a DIVS account.
- `GET /api/v1/auth/sessions/` — list the authenticated account's sessions.
- `DELETE /api/v1/auth/sessions/<session_id>/` — revoke one of the account's sessions.
- `POST /api/v1/auth/logout/` — revoke the current tracked session.
- `GET /api/v1/auth/providers/google/` and `GET /api/v1/auth/providers/phone/` — provider readiness endpoints.

## Security behavior and current limits

- Accounts can be created with an email address, a phone number, or both. Usernames are not part of the account model.
- Password sign-in requires the chosen email address or phone number to be verified.
- Email codes expire after 10 minutes and allow at most five incorrect attempts.
- Code requests are limited to six per destination per rolling 24 hours, with a one-minute resend cooldown. IP-based confirmation/login limits also apply.
- Tracked sessions last as long as the refresh-token lifetime (currently seven days), and revoking a session invalidates its access and refresh use.
- Google ID tokens are verified server-side against the configured client ID. Matching email addresses alone never auto-link a Google identity to an existing account.
- Email delivery requires valid SMTP settings. SMS/OTP delivery is not operational until an SMS provider is selected and integrated.
- Google sign-in can authenticate linked identities, but the separate registration and authenticated account-linking flows have not yet been built.
- Driver registration is separate from the future driver profile and verification records. Saving a registration does not verify a driver or grant work eligibility.
- Client and operations-admin registration, distinct user/driver/client/admin profile models, verification workflows, role authorization, and workspace access gates are not implemented yet.
