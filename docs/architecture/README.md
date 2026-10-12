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
- **Profiles:** separate DriverProfile, ClientProfile, and OperationsProfile records linked to their registration or approved membership. Profile lifecycle status is separate from verification and work eligibility.
- **Driver profiles and employment:** driver information, driving credentials as profile references, and employment history.
- **Verification:** identity, driving licence, and relevant record checks; evidence; review workflows; and verification decisions.
- **Performance and scoring:** evidence-backed performance events and score calculations.
- **Discovery and matching:** driver search, ranking, and job matching.
- **Client requests:** requests to contact or hire drivers and their status.
- **Administration and operations:** operational oversight, user and module administration, verification queues, reporting, and audit review.

These are logical boundaries, not a requirement to create every module before implementation begins. The initial role profile models now live in `backend/apps/profiles/`; automatic profile creation, profile APIs, and access enforcement are still pending.

The backend keeps driver registration in `backend/apps/registrations/` and administration/operations in `backend/apps/operations/`. Driver registration must not own admin invitations, operations applications, approval decisions, or operations permissions. The operations module must not implement driver-registration business rules. Both use the shared identity account model.

## Identity, roles, and permissions

Authentication establishes **who the actor is**. Authorization determines **what that actor may do**.

- Authentication and account identity must support drivers, clients, Admins, and Operators.
- Roles and permissions are cross-cutting concerns. Shared permission primitives may live in `backend/common/permissions/`.
- Admin and operations functionality coordinates authorized oversight across modules, but does not replace module-owned business rules.
- Each module must enforce authorization for its own operations and sensitive data, using shared permission rules where appropriate.
- Operational access is granted only after an invitation-based application is reviewed and approved. A valid invitation code permits an application; it does not grant permissions.
- The system superuser is the initial authority for approving operations applications. Admin and Operator are distinct roles; Operators do not receive superuser privileges.
- Driver and client access rules must also be defined before their features are implemented.
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

Follow the phases in order and finish the registration foundation before building the integrated system:

1. Shared identity and authentication.
2. Driver registration.
3. Client registration.
4. Invitation-based operations registration and application acceptance.
5. Integrated system foundations: driver profile, client profile, and operations/admin profile.
6. Operations roles and permissions, implemented alongside the admin profile and protected capabilities.
7. Driver verification and evidence handling, including future government API integrations.
8. Public driver discovery, filtering, and search.
9. Performance events and scoring.
10. Client-driver engagement records, contact protection, payment references, and audit history.
11. Frontend integration as one simple, coherent experience rather than requiring users to think in terms of separate internal modules.

Client registration does not require client verification. Driver identity and credential verification applies to drivers. Invitations and application acceptance are part of operations registration; the broader role-and-permission system is built later with the integrated operational capabilities.

## Development rules

- Work on `development`; keep `main` untouched unless explicitly approved.
- Build incrementally, with focused tests for each module and its access-control rules.
- Prefer simple, maintainable solutions over unnecessary infrastructure.
- Keep module APIs and service boundaries clear and document important cross-module interactions.

## Deliberate non-goals for this initial architecture

This document does not yet define database models, migrations, detailed API contracts, final authentication integrations, the scoring formula, government API integrations, or every operational workflow. Decide these incrementally before implementing the relevant feature.

## Operations authorization policy

Operations permissions are defined centrally in `backend/apps/operations/permissions.py`. An account does not become an Operator or Admin simply by registering or by validating an invitation.

- **System superuser:** can review pending operations applications and has the Admin capability set.
- **Admin:** activated only after approval; receives the elevated Admin capability set.
- **Operator:** activated only after approval; can access the operations workspace and is not permitted to issue/revoke invitations or approve/reject operations applications.
- **Ordinary account / pending applicant:** has no operations workspace access.

The capability names for driver registration, driver verification review, and performance management are prepared in the policy for later workflow endpoints. They must be enforced by each relevant endpoint when those workflows are implemented; listing a capability is not a substitute for implementing the workflow or its checks.

