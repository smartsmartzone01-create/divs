# DIVS Backend

Django backend with shared identity/authentication and separate domain modules. Driver registration lives in `apps/registrations`; administrative invitations, applications, and approvals live in `apps/operations`. These modules must not own each other's business logic.

## Local setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set a secure `DJANGO_SECRET_KEY`. Environment loading is not automatic yet; export values in your shell or configure a local environment loader.
4. From the `backend/` directory, verify that the committed migration files match the models, apply migrations, and run checks and tests:

   ```bash
   python manage.py makemigrations --check --dry-run
   python manage.py migrate
   python manage.py check
   python manage.py test apps.identity apps.registrations apps.operations
   ```

These commands have not been run against the current online changes yet.

SQLite and local-memory caching are used by default for local development. Configure PostgreSQL and a shared Redis cache for deployment. Rate limiting based on local-memory cache is not shared between multiple application workers.

## Shared authentication routes

- `POST /api/v1/auth/token/` — sign in using `identifier` (verified email or verified phone number) and `password`.
- `GET /api/v1/auth/me/` — retrieve the authenticated account.
- `POST /api/v1/auth/verification/request/` and `POST /api/v1/auth/verification/confirm/` — request and confirm an email or phone verification code.
- `POST /api/v1/auth/token/refresh/` — refresh a token while its tracked device session remains active.
- `GET /api/v1/auth/sessions/`, `DELETE /api/v1/auth/sessions/<session_id>/`, and `POST /api/v1/auth/logout/` — manage tracked sessions.
- `POST /api/v1/auth/providers/google/sign-in/` — validate a Google ID token and sign in only when that Google subject is already linked to a DIVS account.

## Driver registration routes

- `POST /api/v1/registrations/driver/` — create the authenticated account's driver registration.
- `GET /api/v1/registrations/driver/` — retrieve that account's driver registration.
- `PATCH /api/v1/registrations/driver/` — update that account's driver registration.

Driver registration is separate from the future driver profile and verification records. Saving a registration does not verify a driver or grant work eligibility.

## Operations invitation and application routes

- `POST /api/v1/operations/invitations/` — system superuser or approved admin sends an invitation to a specific email for the Admin or Operator role.
- `POST /api/v1/operations/invitations/validate/` — recipient validates the code against the invited email before proceeding.
- `POST /api/v1/operations/invitations/<invitation_id>/revoke/` — revoke an unused invitation.
- `POST /api/v1/operations/applications/` — authenticated account submits a pending application using the invitation code. The account email must match the invited email.
- `GET /api/v1/operations/applications/pending/` — list pending applications for the system superuser.
- `POST /api/v1/operations/applications/<application_id>/review/` — system superuser approves or rejects an application.

Invitation codes are stored as hashes, expire after 24 hours, are tied to the invited email, and are consumed when the application is submitted. A valid code permits an application only; it does not itself grant a role. Approval is a separate step. An approved Admin is activated as a Django superuser, while an approved Operator receives an operations membership without superuser privileges.

## Security behavior and current limits

- Accounts can be created with an email address, a phone number, or both. Usernames are not part of the account model.
- Password sign-in requires the chosen email address or phone number to be verified.
- Email verification codes expire after 10 minutes and allow at most five incorrect attempts.
- Verification sends are limited per destination and have a resend cooldown. Invitation-code validation is also rate-limited.
- Tracked sessions last as long as the refresh-token lifetime (currently seven days), and revoking a session invalidates its access and refresh use.
- Google ID tokens are verified server-side against the configured client ID. Matching email addresses alone never auto-link a Google identity to an existing account.
- Email delivery requires valid SMTP settings. SMS/OTP delivery is not operational until an SMS provider is selected and integrated.
- Google sign-in can authenticate linked identities, but the separate registration and authenticated account-linking flows have not yet been built.
- Client registration, distinct driver/client/admin profile models, verification workflows, and workspace access gates remain future work.
