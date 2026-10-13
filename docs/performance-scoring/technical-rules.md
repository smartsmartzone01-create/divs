# DIVS Performance & Scoring — Technical Rules

**Status:** Scoring-rule approval and one-time event scoring are implemented in the development branch; runtime validation remains pending.  
**Target app:** `backend/apps/performance/`  
**Branch:** `development`

This document describes implemented behavior only. Product requirements and proposed scoring values remain in [`requirements.md`](requirements.md).

## Implemented foundation

### Core records

- `PerformanceEvent` records a reported event against the existing `profiles.DriverProfile`. It does not create a second driver identity.
- Events have a category (`positive`, `negative`, `correction`), optional severity (`minor`, `serious`, `critical`), a lifecycle status, title, description, occurrence time, source type/reference, evidence references, submitter, reviewer, decision timestamp, and decision reason.
- Event statuses currently defined in the model are `submitted`, `under_review`, `more_evidence`, `approved`, and `rejected`. Service-level review transitions and role checks are implemented; API endpoints are not.
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
- Approving a positive or negative event calls the scoring service. A score changes only if a matching Admin-approved rule exists and the driver already has an established calculated score. Without either condition, the event remains approved but receives no score effect yet.

### Score history and override state

- `ScoreHistory` records a score transition with its change type, previous and new score, reason, optional event reference, optional rule reference, actor, and timestamp.
- `change_amount` is derived from the previous and new scores. A baseline entry has no previous score and therefore no delta.
- History rows are intended to be append-only through normal application workflows. Service-layer protections and permissions are not implemented yet.
- `DriverScore.calculated_score` remains the automatic calculation field.
- `DriverScore.manual_override_score` is a separate optional display override. `effective_score` returns the override when present, otherwise the calculated score. The override does not update the automatic calculation.
- The override state includes a reason, Admin account, and timestamp fields. The `override_driver_score` service checks for an approved Operations Admin membership, validates the score and required reason, locks the score row in a transaction, updates only the override fields, and creates a `ScoreHistory` entry in the same transaction. It deliberately does not change availability restrictions. An API endpoint is not implemented yet.
- Both calculated and override scores are constrained to 0–100 when non-null; score-history previous/new values are likewise constrained to 0–100.

### Appeals

- A driver can submit an appeal only for an event with a final approved/rejected decision, and only from the account linked to that event's driver profile.
- An appeal requires a reason and may include evidence references. Only one pending appeal is allowed per event.
- Authorized Operations Admins and Operators can decide a pending appeal as upheld or denied; every decision is recorded in `PerformanceAppealDecision`.
- An upheld appeal sets `correction_required=True`. This explicitly flags follow-up work; it does **not** silently rewrite score history or change a score yet because the score correction/recalculation engine is not implemented.
- Submitting or deciding an appeal does not alter an existing availability restriction. Pending appeals leave current score and restrictions unchanged.

### Availability restrictions

- `AvailabilityRestriction` represents performance-based restrictions independently from driver profile lifecycle and verification status.
- Restriction kinds are `critical_incident` and `low_score`; each has an explicit active/released state, reason, source reference, actor, and timestamps.
- `place_critical_incident_restriction` accepts only a critical-severity event that has not been rejected, places the event into `under_review`, and creates an active restriction. The reason is required to document why precautionary review is warranted. This is not a finding of fault.
- `apply_low_score_restriction` uses the effective score and applies the restriction only when the score is strictly below 40. A score of exactly 40 does not trigger it. An unset score cannot trigger it.
- Only an Operations Admin can release a low-score restriction. Admins and Operators can release a critical-incident restriction with a reason.
- Placement and release decisions are stored in `AvailabilityRestrictionDecision`. A release does not delete the restriction record.
- `has_active_performance_restriction` answers whether any active performance restriction exists. It is a component for future hire-availability checks, not a complete availability/verification decision.
- Score overrides do not automatically release restrictions. A separate authorized release decision is required.

### Scoring rules and calculation

- `PerformanceScoringRule` stores a named rule, event category, severity, signed point change, proposal reason, proposer, approval actor/time, and lifecycle status (`proposed`, `approved`, `retired`).
- Only an Operations Admin may propose, approve, or retire rules. A proposed rule is inactive and has no scoring effect. Point values are not pre-seeded; no point values have been approved by default.
- Positive rules must add points; negative rules must subtract points. A rule must use a whole-number delta from -100 to +100. Only one approved rule may match a given category/severity pair at a time. Retire the existing rule before approving its replacement.
- The calculation service matches an approved event to an approved rule by exact category and severity. Correction events are deliberately excluded from automatic scoring; they require a traceable correction workflow.
- The driver must already have a non-null `calculated_score`. The service does not invent the 80-point baseline from missing history. Baseline assignment still depends on the agreed verification/history eligibility policy.
- Applied changes are clamped to 0–100. The calculated score changes; a manual override remains separate and continues to determine the effective/display score when present.
- `PerformanceEventScoreApplication` records the rule, rule-name snapshot, points, previous/new calculated score, reason, and application time. Its one-to-one event relation prevents the same event from being scored twice through this service. A corresponding `ScoreHistory` row records the transition and actor.
- If the event has no matching approved rule or the driver has no established calculated score, the service returns without changing the score. An Admin can configure a rule later, and the approved event can then be explicitly processed by the scoring service.
- If the resulting effective score is below 40, the scoring service asks the availability workflow to place a low-score restriction when an Operations actor is supplied. Score increases and manual overrides never release existing restrictions automatically.
- Successful appeals still only set `correction_required=True`. Reversing/recalculating an already applied event after an upheld appeal is not implemented yet; the original event application and history must remain intact when that workflow is added.

### Prepared tests

- Model-definition tests cover the score range intent, event categories, effective-score selection, and signed history delta.
- Service tests cover Admin override history creation, preservation of the calculated score, Operator denial, and score/reason validation. Event-review tests cover Operator review, evidence requests, and prevention of silent final-decision replacement. Appeal/availability tests cover driver-only appeal submission, pending-appeal invariants, successful appeal audit, duplicate appeals, the strict below-40 threshold, Admin-only low-score restoration, critical-incident review restrictions, and release history.
- These tests have been committed but have **not** been executed in a local Django environment.

## Not implemented yet

- Runtime validation of the hand-prepared initial migration, verification of model loading, and local test execution. The Performance app is now listed in Django settings.
- Event submission/review APIs, event-submission validation, and endpoint-level permissions. Service-level review decisions are implemented.
- Baseline assignment and its eligibility checks; exact point values remain unapproved and no rules are active by default.
- API endpoint and request/response validation for Admin score overrides; enforcement of append-only history at the database/service boundary beyond the current write-only workflow.
- Runtime validation of migrations 0001–0003 and local execution of all tests. Score correction/recalculation after a successful appeal remains unimplemented.
- Notifications and integration with Operations, Verification, and driver availability.
- Automatic trusted-source checks or government API adapters.

No proposed point values are active by default. An approved event changes a score only after an Admin approves a matching rule and the driver has an established calculated score.

## Safety invariants for subsequent implementation

1. Only approved events may affect scoring.
2. Allegations and unverified reports must not be treated as proven incidents.
3. Preserve original events and decisions; record corrections as new traceable actions.
4. Preserve calculated score history separately from manual overrides.
5. A score override must not automatically clear availability restrictions.
6. Pending appeals leave the current score and restrictions unchanged.
7. Use the existing Operations authorization model and existing driver profiles; do not duplicate accounts, memberships, profiles, or notifications.
8. Keep verification state, performance review state, profile lifecycle, and availability eligibility separate.
