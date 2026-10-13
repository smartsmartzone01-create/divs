# DIVS Performance & Scoring — Technical Rules

**Status:** Model foundation in progress; scoring workflows are not active yet.  
**Target app:** `backend/apps/performance/`  
**Branch:** `development`

This document describes implemented behavior only. Product requirements and proposed scoring values remain in [`requirements.md`](requirements.md).

## Implemented foundation

### Core records

- `PerformanceEvent` records a reported event against the existing `profiles.DriverProfile`. It does not create a second driver identity.
- Events have a category (`positive`, `negative`, `correction`), optional severity (`minor`, `serious`, `critical`), a lifecycle status, title, description, occurrence time, source type/reference, evidence references, submitter, reviewer, decision timestamp, and decision reason.
- Event statuses currently defined in the model are `submitted`, `under_review`, `more_evidence`, `approved`, and `rejected`. Workflow transitions and permissions are not implemented yet.
- `idempotency_key` can hold a source-provided unique key to support future duplicate protection. Full incident deduplication logic is not implemented yet.
- `evidence_references` stores references/metadata only. Do not put raw government records, identity numbers, or sensitive source payloads in it.
- `DriverScore` is a one-to-one record for an existing driver profile. `calculated_score` may be null until baseline eligibility and history-review rules are finalized. Null means “not yet established,” not zero.
- A database constraint restricts non-null calculated scores to 0–100.

### Event review workflow

- `PerformanceEventReview` stores each reviewer decision as a separate historical row with reviewer, reason, optional requested evidence, and timestamp.
- The `review_performance_event` service permits approved Operations Admins and Operators to approve, reject, or request more evidence.
- A reason is required for every decision; requesting more evidence also requires a description of what is needed.
- The current event status and latest decision fields are updated transactionally with the review-history insert.
- Approved and rejected events are final in this service; a later challenge must use the planned appeal/correction workflow rather than silently replacing the original decision.
- Event approval currently records a decision only. It does not change a score because approved scoring rules and score calculation are not implemented.

### Score history and override state

- `ScoreHistory` records a score transition with its change type, previous and new score, reason, optional event reference, optional rule reference, actor, and timestamp.
- `change_amount` is derived from the previous and new scores. A baseline entry has no previous score and therefore no delta.
- History rows are intended to be append-only through normal application workflows. Service-layer protections and permissions are not implemented yet.
- `DriverScore.calculated_score` remains the automatic calculation field.
- `DriverScore.manual_override_score` is a separate optional display override. `effective_score` returns the override when present, otherwise the calculated score. The override does not update the automatic calculation.
- The override state includes a reason, Admin account, and timestamp fields. The `override_driver_score` service checks for an approved Operations Admin membership, validates the score and required reason, locks the score row in a transaction, updates only the override fields, and creates a `ScoreHistory` entry in the same transaction. It deliberately does not change availability restrictions. An API endpoint is not implemented yet.
- Both calculated and override scores are constrained to 0–100 when non-null; score-history previous/new values are likewise constrained to 0–100.

### Prepared tests

- Model-definition tests cover the score range intent, event categories, effective-score selection, and signed history delta.
- Service tests cover Admin override history creation, preservation of the calculated score, Operator denial, and score/reason validation. Event-review tests cover Operator review, evidence requests, and prevention of silent final-decision replacement.
- These tests have been committed but have **not** been executed in a local Django environment.

## Not implemented yet

- Runtime validation of the hand-prepared initial migration, verification of model loading, and local test execution. The Performance app is now listed in Django settings.
- Event submission/review APIs, event-submission validation, and endpoint-level permissions. Service-level review decisions are implemented.
- Active scoring rules, event point values, score calculation, or baseline assignment.
- API endpoint and request/response validation for Admin score overrides; enforcement of append-only history at the database/service boundary beyond the current write-only workflow.
- Appeals, correction processing, critical-incident restrictions, low-score restrictions, and restoration approvals.
- Notifications and integration with Operations, Verification, and driver availability.
- Automatic trusted-source checks or government API adapters.

No proposed point values are active. No event currently changes a score through an implemented workflow.

## Safety invariants for subsequent implementation

1. Only approved events may affect scoring.
2. Allegations and unverified reports must not be treated as proven incidents.
3. Preserve original events and decisions; record corrections as new traceable actions.
4. Preserve calculated score history separately from manual overrides.
5. A score override must not automatically clear availability restrictions.
6. Pending appeals leave the current score and restrictions unchanged.
7. Use the existing Operations authorization model and existing driver profiles; do not duplicate accounts, memberships, profiles, or notifications.
8. Keep verification state, performance review state, profile lifecycle, and availability eligibility separate.
