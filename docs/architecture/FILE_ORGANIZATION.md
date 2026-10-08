# DIVS File Organization

This document defines the initial backend folder organization for DIVS. The project uses a **modular monolith**: modules live in one backend codebase, but each module owns its implementation and domain rules.

## Backend structure

```text
backend/
├── apps/
│   └── <module>/
│       ├── models/
│       ├── services/
│       ├── repositories/
│       ├── serializers/
│       ├── views/
│       ├── throttles/
│       ├── api/
│       ├── tests/
│       └── urls.py
│
├── common/
│   ├── permissions/
│   ├── throttles/        # shared only
│   ├── exceptions/
│   ├── validators/
│   ├── utils/
│   └── ...
│
└── routes/
```

The tree is the standard starting pattern. Add files or subfolders when a module genuinely needs them; do not create empty folders only to satisfy the template.

## Module ownership: `backend/apps/<module>/`

Each module owns code specific to its business capability.

- `models/` — Django models owned by this module.
- `services/` — use cases and business operations.
- `repositories/` — data-access logic when a repository layer is useful; avoid unnecessary abstraction.
- `serializers/` — request/response validation and serialization for the module.
- `views/` — request handling and coordination with services.
- `throttles/` — rate-limiting rules specific to this module.
- `api/` — module-specific API organization, such as versioned or grouped endpoints when needed.
- `tests/` — tests for the module's rules, services, API behavior, and permissions.
- `urls.py` — module-owned URL patterns exposed to the project router.

A module may organize these areas into further subfolders as it grows. Keep business rules in the module that owns them rather than moving them to `common/` merely because another module needs to call them.

## Shared functionality: `backend/common/`

`common/` is for cross-cutting code that is intentionally reused across the project.

- `permissions/` — shared permission primitives and reusable authorization helpers.
- `throttles/` — throttles that are genuinely shared across multiple modules. Module-specific throttles stay in the owning module.
- `exceptions/` — common API or application exception handling.
- `validators/` — reusable validators that are not specific to one domain.
- `utils/` — small, domain-neutral utilities.
- Additional subfolders may be added when a real shared need exists.

### Rules for common code

1. Do not use `common/` as a general dumping ground.
2. Keep domain-specific behavior inside its owning module.
3. Shared permission helpers provide reusable rules, but each module remains responsible for enforcing authorization on its own operations and data.
4. Avoid circular dependencies between modules. Prefer a clear service boundary or a small, explicit shared contract.
5. Move code into `common/` only when its cross-module purpose is clear and stable.

## Project routing: `backend/routes/`

The `routes/` package is the project-level entry point for URL routing. It connects the top-level URL configuration to module-owned URL patterns. Feature-specific endpoints and URL definitions should remain with their module in `apps/<module>/urls.py`.

## Admin and operations placement

Admin and operations functionality may need authorized access across several modules, but it must not become the owner of all module business logic.

- Administrative workflows and operational screens belong to the relevant admin/operations module.
- Shared authorization primitives belong in `common/permissions/`.
- The module that owns a capability remains responsible for enforcing access to its data and actions.
- Audit records must capture important administrative actions and verification decisions. The exact audit implementation can be established before that module is built.

## Initial module examples

The architecture document defines the initial domain boundaries. As they are implemented, modules may include identity/accounts, driver profiles and employment, verification, performance/scoring, discovery/matching, client requests, and admin/operations.

Use clear, consistent module names. Do not create all modules in advance if they have no implementation yet.

## Frontend organization

The frontend uses Next.js and TypeScript. Its detailed folder structure is intentionally not specified by this backend organization document; define it in a separate frontend-specific document when the frontend structure is ready to be established.

## Change discipline

- Make structural changes incrementally and explain why a new shared or module-owned folder is needed.
- Keep the backend modular rather than splitting into microservices without a demonstrated need.
- Add tests alongside module functionality.
- Work on `development`; do not modify `main` without explicit approval.
