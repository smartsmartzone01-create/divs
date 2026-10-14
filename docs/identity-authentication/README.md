# DIVS Identity & Authentication

## Scope and ownership

The identity module authenticates a person; it does not decide whether that person is a driver, client, operator, or administrator. Driver and client registration belong to the registrations module. Operations membership and approval belong to the operations module. The public discovery endpoint remains accessible without an account.

Identity must not create duplicate profile or role records. A Google first sign-in may create a bare account identity, and the appropriate registration workflow must still be completed before the person can use role-specific workspace features.

## Supported authentication flows

- Email + password, after the email address is verified.
- Phone + password, after the phone number is verified.
- Google sign-in using a server-verified Google ID token and a configured OAuth client ID. Google sign-in does not require a second DIVS one-time code.
- Short-lived access JWTs and rotating refresh tokens tied to tracked server-side sessions.
- Current-account endpoint, session listing, single-session revocation, and current-session logout.
- Email/phone verification codes with expiry, hashed storage, bounded attempts, resend throttling, and separate code purposes.
- Email or verified-phone password reset using a purpose-scoped code. A successful reset revokes all tracked sessions.
- Google account linking only when the caller is authenticated. Matching email alone never silently merges an existing account.

## Security rules

- Do not expose whether an email is registered through password-reset responses.
- Never trust Google token claims without signature and audience validation.
- Never auto-merge a Google identity into an existing password account based on matching email alone.
- Do not mark a phone number verified unless a real SMS adapter delivered the code and DIVS successfully checked the submitted code.
- Never store raw verification codes. Store password-hashed code values and enforce expiry and attempt limits.
- Do not log passwords, raw OTP values, access tokens, refresh tokens, or full provider credentials.
- Refresh tokens must reference an active tracked session. Revoked/expired sessions must fail authentication and refresh.
- Production throttling must use a shared cache such as Redis; process-local memory cache is for local development only.
- Keep secret keys, OAuth credentials, email credentials, and SMS credentials in environment variables.

## SMS provider adapter contract

Set `SMS_OTP_PROVIDER_CLASS` to a Python class import path. The class is instantiated by DIVS and must implement:

```python
send_verification_code(phone_number, code, expires_in_seconds=600)
```

The adapter must deliver the provided code, raise an exception on delivery failure, and never log the code. Provider selection and credentials are deployment configuration; do not mark phone verification as production-ready until a real adapter has been configured and tested end to end.

## Routes

- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/token/`
- `POST /api/v1/auth/token/refresh/`
- `GET /api/v1/auth/me/`
- `GET /api/v1/auth/sessions/`
- `DELETE /api/v1/auth/sessions/<session_id>/`
- `POST /api/v1/auth/logout/`
- `POST /api/v1/auth/verification/request/`
- `POST /api/v1/auth/verification/confirm/`
- `POST /api/v1/auth/providers/google/sign-in/`
- `GET /api/v1/auth/providers/google/`
- `GET /api/v1/auth/providers/phone/`
- `POST /api/v1/auth/password-reset/request/`
- `POST /api/v1/auth/password-reset/confirm/`

## Remaining environment and validation work

- Configure real email delivery, Google OAuth client ID, and a real SMS provider adapter in local/staging environments.
- Run migrations and all identity tests locally.
- Test Google credentials against the configured OAuth audience and test provider callbacks/delivery with real test credentials.
- Verify production HTTPS, trusted proxy/IP settings, CORS/CSRF policy where applicable, secure deployment settings, and Redis-backed throttling.
- Review account linking and recovery UX with the frontend once screens are implemented.

## Completion checklist for local verification

Use this checklist after installing the backend dependencies and applying the migrations locally:

- [ ] A new email account can register, request an email code, verify the email, and sign in with email + password.
- [ ] A phone account can register, receive a code through the configured SMS adapter, verify the phone, and sign in with phone + password.
- [ ] Unverified contacts and incorrect passwords cannot sign in.
- [ ] A first-time Google identity creates a bare identity account and signs in without a DIVS OTP.
- [ ] A Google identity matching an existing password account is not silently merged; signing in to that account and linking Google is required.
- [ ] Password-reset codes cannot be reused as contact-verification codes, expire, and stop working after the attempt limit.
- [ ] A successful password reset changes the password and revokes all active sessions.
- [ ] Revoking a device session blocks both access-token use and refresh-token use.
- [ ] Public verification/reset responses do not disclose whether an account exists.
- [ ] The frontend keeps JWTs in HttpOnly cookies, refreshes expired access tokens, and signs out cleanly.
- [ ] Run backend migrations/checks/tests and frontend lint/typecheck/build. These have **not** been run as part of the online code changes.

