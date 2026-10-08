# DIVS Architecture

DIVS (Driver Identification and Verification System) is a modular application for driver registration, identity and credential verification, performance records, and driver discovery.

## Initial technology direction

- Backend: Python, Django, Django REST Framework, and PostgreSQL.
- Frontend: Next.js and TypeScript.
- Architecture: modular monolith; modules own their APIs, serializers, views, services, URLs, tests, and domain rules.
- Shared code belongs in a common module only when it is genuinely cross-cutting.

## Initial domain boundaries

- Identity and accounts
- Driver profiles and employment history
- Verification of identity, driving licences, and relevant records
- Evidence-backed performance events and driver scores
- Driver discovery and matching
- Client requests to hire or contact drivers
- Administration, verification operations, and audit trails

## Important rules

- Government sources are authoritative when an official integration is available.
- Manual review must distinguish submitted evidence, pending review, and verified information.
- An accident record alone does not establish fault and must not automatically reduce a driver's score.
- Scores reflect supported performance evidence; ranking and job matching are separate concerns.
- Administrative changes and verification decisions must be auditable.
- Keep `main` untouched during development. Work on `development` and make small, reviewable commits.

## Deliberate non-goals for this first step

This document does not define database models, migrations, API contracts, authentication integrations, scoring formulas, or government API integrations. Those decisions should be made incrementally before implementation.
