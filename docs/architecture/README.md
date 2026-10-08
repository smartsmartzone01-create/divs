# DIVS Architecture

DIVS (Driver Identification and Verification System) is a modular application for driver registration, identity and credential verification, performance records, and driver discovery.

## Architecture approach

- Use a **modular monolith**: one application organised into modules with clear responsibilities and boundaries.
- Backend: Python, Django, Django REST Framework, and PostgreSQL.
- Frontend: Next.js and TypeScript.
- Each module owns its domain rules and its related models, services, repositories, serializers, views, throttles, API routes, URLs, and tests, as applicable.
- Cross-cutting functionality belongs in `backend/common/` only when it is genuinely shared by multiple modules.
- Keep module-to-module dependencies explicit. Avoid duplicating domain rules in shared code or allowing one module to directly own another module's business logic.

## Domain modules

The following are initial domain boundaries. They can become individual apps under `backend/apps/` as implementation proceeds.

- **Identity and accounts:** registration, authentication, account recovery, and account identity.
- **Driver profiles and employment:** driver information, driving credentials as profile references, and employment history.
- **Verification:** identity, driving licence, and relevant record checks; evidence; review workflows; and verification decisions.
- **Performance and scoring:** evidence-backed performance events and score calculations.
- **Discovery and matching:** driver search, ranking, and job matching.
- **Client requests:** requests to contact or hire drivers and their status.
- **Administration and operations:** operational oversight, user and module administration, verification queues, reporting, and audit review.

These are logical boundaries, not a requirement to create every module before implementation begins.

## Identity, roles, and permissions

Authentication establishes **who the actor is**. Authorization determines **what that actor may do**.

- Authentication and account identity must support drivers, clients, administrators, and verification officers.
- Roles and permissions are cross-cutting concerns. Shared permission primitives may live in `backend/common/permissions/`.
- Admin and operations functionality coordinates authorized oversight across modules, but does not replace module-owned business rules.
- Each module must enforce authorization for its own operations and sensitive data, using shared permission rules where appropriate.
- Initial operational roles include Operations Admin and Verification Officer. Driver and client access rules must also be defined before their features are implemented.
- Sensitive identity, licence, accident, and verification evidence must have explicit access rules and appropriate retention safeguards.

## Verification and evidence rules

- Government sources are authoritative when an official integration is available.
- Keep official verification distinguishable from manual review.
- Record states must clearly distinguish submitted evidence, pending review, manually verified, officially verified, rejected, and expired information where those states apply.
- Do not present submitted or pending information as verified.
- Verification decisions, evidence changes, and administrative actions must be auditable.

## Performance, scoring, and discovery

- Scores must be based on supported performance evidence.
- Record the evidence and applicable rule behind each score change so it can be reviewed and corrected when necessary.
- An accident record alone does not establish fault and must not automatically reduce a driver's score.
- Scoring, search ranking, and job matching are separate concerns; a numerical score must not silently become the search ranking formula.
- Provide a review or correction path for disputed or inaccurate information.

## Suggested implementation order

1. Identity and authentication.
2. Shared authorization foundations and role definitions.
3. Driver profiles and employment history.
4. Verification workflows and evidence handling.
5. Performance events and scoring.
6. Driver discovery and matching.
7. Client hire/contact requests.
8. Expanded admin operations, reporting, and audit tools.

Admin permissions, audit requirements, and privacy boundaries should be considered from the start, even though the complete admin dashboard is implemented later.

## Development rules

- Work on `development`; keep `main` untouched unless explicitly approved.
- Build incrementally, with focused tests for each module and its access-control rules.
- Prefer simple, maintainable solutions over unnecessary infrastructure.
- Keep module APIs and service boundaries clear and document important cross-module interactions.

## Deliberate non-goals for this initial architecture

This document does not yet define database models, migrations, detailed API contracts, final authentication integrations, the scoring formula, government API integrations, or every operational workflow. Decide these incrementally before implementing the relevant feature.
