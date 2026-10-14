# Frontend Feature Modules

Feature modules mirror the Django domain boundaries, but contain presentation and API-client code only. Django remains authoritative for validation, permissions, verification decisions, availability, and scoring.

Add a module when its UI work begins. Use only the subfolders that module needs; do not create empty boilerplate folders in advance.

A typical feature may use:

```text
feature-name/
├── components/   # Feature-specific UI
├── hooks/        # Feature-specific React hooks
├── services/     # Calls to the shared API client
├── schemas/      # Client-side form validation only
├── types/        # Feature-specific request/response types
└── tests/        # Feature component and service tests
```

## Domain ownership

- `identity/`: sign-in, sign-out, account recovery and session UI.
- `registrations/`: driver, client and operations application forms.
- `profiles/`: driver/client profiles and approved Operations profile screens.
- `verification/`: verification status and authorized evidence/review screens.
- `discovery/`: public driver listing, filters and privacy-safe driver cards.
- `performance/`: event history, score display, appeals and corrections.
- `client-requests/`: contact/hiring requests and payment-gated contact UI.
- `operations/`: Admin and Operator workspaces.

Keep shared HTTP behavior in `src/lib/api/`. Feature services should call that client rather than reimplementing fetch/error handling. Do not put secrets or authorization decisions in frontend code.
