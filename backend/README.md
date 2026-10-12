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
   python manage.py test apps.identity apps.registrations apps.operations apps.profiles common.tests
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

## Driver registration routes

- `POST /api/v1/registrations/driver/` — create the authenticated account's driver registration.
- `GET /api/v1/registrations/driver/` — retrieve that account's driver registration.
- `PATCH /api/v1/registrations/driver/` — update that account's driver registration.

Driver registration is separate from the future driver profile and verification records. Saving a registration does not verify a driver or grant work eligibility.

## Client registration routes

- `POST /api/v1/registrations/client/` — create the authenticated account's client registration as an individual or company.
- `GET /api/v1/registrations/client/` — retrieve that account's client registration.
- `PATCH /api/v1/registrations/client/` — update that account's client registration.

Client registration records the client type, person/company name, primary contact, email, country, region, and optional alternative contacts. Client verification is not part of this registration flow. The same shared account can register as both a driver and a client; each role has its own registration record.

## Role profile foundation

- `apps.profiles.DriverProfile` links one-to-one to a driver registration.
- `apps.profiles.ClientProfile` links one-to-one to a client registration.
- `apps.profiles.OperationsProfile` links one-to-one to an approved operations membership.
- Each profile has its own UUID, lifecycle status (`active`, `suspended`, or `closed`), and timestamps. The shared account is resolved through its linked registration or membership, avoiding a second account foreign key that could disagree.
- Profile status is not verification status or hiring eligibility. Those rules will be handled separately.
- Profile creation is automated on successful driver/client registration and successful operations approval.
- Shared authorization lives in `common/permissions.py` (`HasRequiredProfile`) and `common/views.py` (`RoleProtectedAPIView`). A protected view declares `required_profile_type` as `driver`, `client`, or `operations`; access is granted only when the authenticated account has an active matching profile. The system superuser can access the operations area but does not automatically gain driver or client profile access.
- Registration endpoints remain outside this protected base so a person can register before they have a profile. The policy foundation is implemented and has tests; the driver profile retrieval endpoint is the next step.

## Operations access, invitation and application routes

- `GET /api/v1/operations/me/` — return the signed-in approved operations role and its explicit capability list. This is a policy overview; it does not imply all listed driver workflows have been implemented.
- `POST /api/v1/operations/invitations/` — system superuser or approved admin sends an invitation to a specific email for the Admin or Operator role.
- `POST /api/v1/operations/invitations/validate/` — recipient validates the code against the invited email before proceeding.
- `POST /api/v1/operations/invitations/<invitation_id>/revoke/` — revoke an unused invitation.
- `POST /api/v1/operations/applications/` — authenticated account submits a pending application using the invitation code. The account email must match the invited email.
- `GET /api/v1/operations/applications/pending/` — list pending applications for the system superuser.
- `POST /api/v1/operations/applications/<application_id>/review/` — system superuser approves or rejects an application.

Invitation codes are stored as hashes, expire after 24 hours, are tied to the invited email, and are consumed when the application is submitted. A valid code permits an application only; it does not itself grant a role. Approval is a separate step. An approved Admin is activated as a Django superuser, while an approved Operator receives an operations membership without superuser privileges. The current capability policy lets Operators access the operations workspace and reserves invitation management and operations-application review for the Admin/system-superuser path. Driver registration, verification review, and performance capabilities are defined for future endpoints but do not become usable until those workflows enforce the policy.

## Security behavior and current limits

- Accounts can be created with an email address, a phone number, or both. Usernames are not part of the account model.
- Password sign-in requires the chosen email address or phone number to be verified.
- Email verification codes expire after 10 minutes and allow at most five incorrect attempts.
- Verification sends are limited per destination and have a resend cooldown. Invitation-code validation is also rate-limited.
- Tracked sessions last as long as the refresh-token lifetime (currently seven days), and revoking a session invalidates its access and refresh use.
- Google ID tokens are verified server-side against the configured client ID. Matching email addresses alone never auto-link a Google identity to an existing account.
- Email delivery requires valid SMTP settings. SMS/OTP delivery is not operational until an SMS provider is selected and integrated.
- Google sign-in can authenticate linked identities, but the separate registration and authenticated account-linking flows have not yet been built.
- The initial DriverProfile, ClientProfile, and OperationsProfile models now exist in `apps.profiles`. They have separate UUIDs and lifecycle status fields, and each links to its role registration or approved operations membership rather than duplicating account identity or registration details. Driver and client profiles are created in the same transaction as their registration; an operations profile is created in the same transaction as membership approval. The shared role-access policy and protected-view base are implemented; profile retrieval APIs are still future work.
