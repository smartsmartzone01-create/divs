# DIVS Frontend

The DIVS frontend is a **Next.js App Router application written in strict TypeScript**. It is a separate frontend application that communicates with the Django REST API; it does not contain backend business rules or connect directly to PostgreSQL.

## Requirements

- Git
- Node.js **24.18.0** (pinned in `.nvmrc`)
- pnpm **11.15.1** (pinned in `package.json`)
- The DIVS Django backend for API-connected features
- A Vercel account when deploying the frontend

The Node.js version is managed independently from Python/Django. Install Node.js first, then enable pnpm through Corepack if your Node distribution includes it. If Corepack is not available, install the pinned pnpm release using the official pnpm installation instructions.

## Install and run locally

Open a terminal in the `frontend/` directory:

```powershell
node --version
pnpm --version
pnpm install
Copy-Item .env.example .env.local
pnpm dev
```

Open http://localhost:3000.

The first install creates `pnpm-lock.yaml`. Commit that lockfile after installation so local machines and Vercel use the same dependency resolution. For a clean, reproducible install after the lockfile exists, use:

```powershell
pnpm install --frozen-lockfile
```

Useful commands:

```powershell
pnpm dev
pnpm lint
pnpm typecheck
pnpm check
pnpm build
pnpm start
```

Run `pnpm build` before treating a change as ready. The scaffold has not been installed or runtime-tested from this repository environment.

## Environment variables

`.env.example` documents the Django API base URL and the public Google Identity Services client ID. Copy it to `.env.local` for local work and adjust the URL if the backend runs elsewhere:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
DIVS_API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_GOOGLE_OIDC_CLIENT_ID=
```

The frontend uses a same-origin Next.js API proxy for Django requests. Access and refresh JWTs are stored in `HttpOnly`, `SameSite=Lax` cookies and are never returned to browser JavaScript. The proxy refreshes expired access tokens and revokes/clears cookies on logout. `DIVS_API_BASE_URL` is server-only; the Google client ID is public by design. Configure the matching `GOOGLE_OIDC_CLIENT_ID` in the Django environment.

Only values intended to be visible to the browser may use the `NEXT_PUBLIC_` prefix. **Never place passwords, private API keys, signing secrets, or database credentials in a `NEXT_PUBLIC_` variable.** Keep local `.env.local` files out of Git.

## Vercel deployment

1. Push the `development` branch to GitHub and import the DIVS repository in Vercel.
2. Set the Vercel **Root Directory** to `frontend`.
3. Use the Next.js framework preset. Vercel should detect the build command and output settings automatically.
4. Configure `NEXT_PUBLIC_API_BASE_URL` separately for Preview and Production, using the reachable HTTPS URL for the deployed Django API.
5. Deploy the development branch as a Preview deployment while building and checking features. Do not make `development` the Production Branch or change `main` without explicit project approval.
6. Before release, check backend CORS/CSRF and authentication settings against the actual frontend origin; do not use permissive production CORS settings.

Vercel builds the frontend; it does not host the Django API or PostgreSQL database as part of this frontend configuration. The API must be deployed and reachable independently.

## File organization

```text
frontend/
├── src/
│   ├── app/                       # Next.js routes, layouts, loading/error boundaries
│   ├── features/
│   │   ├── identity/              # Sign-in, sessions, account recovery
│   │   ├── registrations/         # Driver, client and operations applications
│   │   ├── profiles/              # Role-specific profile screens
│   │   ├── verification/          # Driver verification status and evidence workflow UI
│   │   ├── discovery/             # Public driver search, filters and driver cards
│   │   ├── performance/            # Scores, events, appeals and history
│   │   ├── client-requests/        # Contact/hiring requests and payment-gated contact
│   │   └── operations/             # Admin and Operator workspace
│   ├── components/
│   │   ├── ui/                    # Reusable visual primitives
│   │   └── layout/                # Header, navigation, page shells
│   ├── lib/
│   │   ├── api/                   # Shared HTTP client and API error handling
│   │   └── config/                # Environment and app configuration
│   ├── hooks/                     # Truly shared React hooks
│   ├── providers/                 # Shared React context providers
│   └── types/                     # Shared cross-feature TypeScript types only
├── public/                        # Static assets
├── .env.example
├── package.json
├── pnpm-lock.yaml                 # Generated and committed after pnpm install
├── tsconfig.json
└── next.config.ts
```

Each feature should own its feature-specific components, API service functions, types, validation schemas, hooks, and tests as those are introduced. Keep route files in `src/app/` thin: they should compose feature components rather than own domain rules. Shared folders are for genuinely reusable code; do not duplicate backend validation or scoring rules in the browser.

## Identity routes now scaffolded

- `/sign-in` — email or verified-phone password sign-in, plus Google sign-in when configured.
- `/register` — create a shared identity without selecting a role.
- `/verify` — request and confirm email or phone verification codes.
- `/forgot-password` — request and confirm password recovery by verified email or phone.
- `/account` — review contact verification and manage active sessions, including revocation and logout.
- `/api/auth/[...path]` and `/api/backend/[...path]` — same-origin server-side proxies; JWTs stay in HttpOnly cookies.

These screens and proxy routes are code-complete foundations, but frontend dependency installation, type checking, linting, production build, backend integration, and real provider tests have not been run in this environment.

## Dependency policy

- Use pnpm for all JavaScript package installation and scripts.
- Keep `pnpm-lock.yaml` committed and use `pnpm install --frozen-lockfile` in repeatable builds.
- Prefer the built-in `fetch` API for Django requests; add third-party packages only when a concrete need appears.
- Keep strict TypeScript enabled.
- Do not commit `.env.local`, `.vercel/`, `node_modules/`, or `.next/`.
- Keep frontend work on `development`; `main` remains untouched unless explicitly approved.
