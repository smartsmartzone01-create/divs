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
   python manage.py test apps.identity apps.registrations apps.operations apps.profiles apps.verification common.tests
   ```

These commands have not been run against the current online changes yet.

SQLite and local-memory caching are used by default for local development. Configure PostgreSQL and a shared Redis cache for deployment. Rate limiting based on local-memory cache is not shared between multiple application workers.

## Shared authentication routes

- `POST /api/v1/auth/register/` — create a shared identity account without choosing a role; role-specific registration remains separate.
- `POST /api/v1/auth/token/` — sign in using `identifier` (verified email or verified phone number) and `password`.
- `GET /api/v1/auth/me/` — retrieve the authenticated account.
- `POST /api/v1/auth/verification/request/` and `POST /api/v1/auth/verification/confirm/` — request and confirm an email or phone verification code.
- `POST /api/v1/auth/token/refresh/` — refresh a token while its tracked device session remains active.
- `GET /api/v1/auth/sessions/`, `DELETE /api/v1/auth/sessions/<session_id>/`, and `POST /api/v1/auth/logout/` — manage tracked sessions.
- `POST /api/v1/auth/providers/google/sign-in/` — validate a Google ID token and sign in only when that Google subject is already linked to a DIVS account.

## Driver registration and profile

- `POST /api/v1/registrations/driver/` — create the authenticated account's driver registration.
- `GET /api/v1/registrations/driver/` — retrieve that account's driver registration.
- `PATCH /api/v1/registrations/driver/` — update that account's driver registration.
- `GET /api/v1/profiles/driver/` — retrieve the driver's own profile metadata and nested registration details.

Registration and profile existence do not verify a driver or grant work eligibility. The profile endpoint is read-only and uses the shared role-protected API base.

## Driver verification

- `GET /api/v1/verification/driver/me/` — return the signed-in driver's own overall verification state, four check states, and current discoverability gate.
- `POST /api/v1/verification/operations/checks/<check_id>/review/` — allow an active operations profile to record a manual outcome for one check.

The initial check types are national identity, driving licence, traffic/police records, and accident records. A new driver profile automatically receives a verification record and one pending row for each check. Overall verification becomes approved only when all four checks pass; a failed check rejects it. This is a verification gate, not the full discovery implementation.

**Data minimization rule:** verification stores only check type, status, a limited result code, method, timestamps, and reviewer. It has no fields for national ID numbers, licence numbers, dates of birth, free-text notes, government response payloads, police narratives, or accident details. Government API adapters are not connected yet; manual review is the current workflow, and a future adapter must translate the source response into an allowed result code and discard the raw response.

## Client registration and profile foundation

- `POST /api/v1/registrations/client/` — create the authenticated account's client registration as an individual or company.
- `GET /api/v1/registrations/client/` — retrieve that account's client registration.
- `PATCH /api/v1/registrations/client/` — update that account's client registration.

Client registration records client type, name, primary contact, email, country, region, and optional alternative contacts. Client verification is not part of this flow. The same account can have driver and client profiles.

## Shared profile access

- `apps.profiles.DriverProfile`, `ClientProfile`, and `OperationsProfile` each have a UUID, lifecycle status (`active`, `suspended`, or `closed`), and timestamps.
- Shared authorization lives in `common/permissions.py` and `common/views.py`. Protected endpoints declare a required profile type; registration endpoints remain accessible before role profiles exist.
- Profile lifecycle status is separate from driver verification and future work eligibility. The driver discovery endpoint will later enforce verification and other visibility rules.

## Operations access, invitation and application routes

- `GET /api/v1/operations/me/` — return the signed-in approved operations role and its explicit capability list.
- `POST /api/v1/operations/invitations/` — system superuser or approved admin sends an invitation to a specific email for the Admin or Operator role.
- `POST /api/v1/operations/invitations/validate/` — recipient validates the code against the invited email.
- `POST /api/v1/operations/invitations/<invitation_id>/revoke/` — revoke an unused invitation.
- `POST /api/v1/operations/applications/` — submit an application using an invitation code.
- `GET /api/v1/operations/applications/pending/` and `POST /api/v1/operations/applications/<application_id>/review/` — superuser reviews pending applications.

Invitation codes are hashed, tied to the invited email, and consumed when an application is submitted. The current implementation expires invitations after 24 hours. Approval is a separate step; approved Admins are activated as Django superusers, while Operators receive operations membership without superuser privileges.

## Security behavior and current limits

- Accounts can be created with an email address, a phone number, or both. Usernames are not part of the account model.
- Password sign-in requires the chosen email address or phone number to be verified.
- Email verification codes expire after 10 minutes and allow at most five incorrect attempts.
- Verification sends are limited per destination and have a resend cooldown. Invitation-code validation is also rate-limited.
- Tracked sessions last as long as the refresh-token lifetime (currently seven days), and revoking a session invalidates its access and refresh use.
- Google ID tokens are verified server-side against the configured client ID. Matching email addresses alone never auto-link a Google identity to an existing account.
- Email/SMS delivery and government API integration require provider configuration and are not claimed to be operational until integrated and tested.
