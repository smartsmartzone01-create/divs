# DIVS Performance & Scoring — Technical Rules

**Status:** Service layer and an initial REST API layer are committed on `development`; runtime validation remains pending.  
**Target app:** `backend/apps/performance/`  
**Branch:** `development`

This document describes implemented behavior only. Product requirements and proposed scoring values remain in [`requirements.md`](requirements.md).

## Implemented foundation

### Core records

- `PerformanceEvent` records a reported event against the existing `profiles.DriverProfile`. It does not create a second driver identity.
- Events have a category (`positive`, `negative`, `correction`), a stable `event_code` used for rule matching, optional severity (`minor`, `serious`, `critical`), a lifecycle status, title, description, occurrence time, source type/reference, evidence references, submitter, reviewer, decision timestamp, and decision reason.
- Event statuses currently defined in the model are `submitted`, `under_review`, `more_evidence`, `approved`, and `rejected`. Service-level review transitions and role checks are implemented; API endpoints are not.
- `idempotency_key` can hold a source-provided unique key to support future duplicate protection. Full incident deduplication logic is not implemented yet.
- `evidence_references` stores references/metadata only. Do not put raw government records, identity numbers, or sensitive source payloads in it.
- `DriverScore` is a one-to-one record for an existing driver profile. `calculated_score` may be null until an Admin establishes an eligible baseline. Null means “not yet established,” not zero.
- A database constraint restricts non-null calculated scores to 0–100.

### Baseline establishment

- `establish_driver_baseline` is Admin-only and assigns the agreed baseline of 80 only after the caller explicitly confirms driver verification, review of applicable history, and that applicable history was found.
- A baseline requires a reason and creates a `ScoreHistory` entry with no previous score.
- If no applicable history is found, the service rejects baseline establishment and leaves the score unset. This is a conservative interim behavior; the product policy for drivers with no history remains unresolved.
- Baseline establishment is blocked if a calculated score or any score-history entry already exists. It does not overwrite a score or act as a recalculation.

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
- The override state includes a reason, Admin account, and timestamp fields. The `override_driver_score` service checks for an approved Operations Admin membership, validates the score and required reason, locks the score row in a transaction, updates only the override fields, and creates a `ScoreHistory` entry in the same transaction. It deliberately does not change availability restrictions. An API endpoint is now available under the Performance API.
- Both calculated and override scores are constrained to 0–100 when non-null; score-history previous/new values are likewise constrained to 0–100.

### Appeals

- A driver can submit an appeal only for an event with a final approved/rejected decision, and only from the account linked to that event's driver profile.
- An appeal requires a reason and may include evidence references. Only one pending appeal is allowed per event.
- Authorized Operations Admins and Operators can decide a pending appeal as upheld or denied; every decision is recorded in `PerformanceAppealDecision`.
- An upheld appeal sets `correction_required=True`. An Operations Admin must then explicitly run the score-correction service with a reason. The service recalculates the automatic score by replaying immutable event applications while excluding the overturned event and any previously corrected events. It creates a separate `PerformanceScoreCorrection` record and a `ScoreHistory` correction entry when the calculated score changes. The original event, rule application, and historical snapshots are not rewritten. If the appealed event never affected a score, the workflow records that outcome without inventing a score change. Manual overrides and active availability restrictions are never automatically removed.
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

- `PerformanceScoringRule` stores a named rule, event category, stable event code, severity, signed point change, proposal reason, proposer, approval actor/time, and lifecycle status (`proposed`, `approved`, `retired`).
- Only an Operations Admin may propose, approve, or retire rules. A proposed rule is inactive and has no scoring effect. Point values are not pre-seeded; no point values have been approved by default.
- Positive rules must add points; negative rules must subtract points. A rule must use a whole-number delta from -100 to +100. Only one approved rule may match a given category/event-code/severity combination at a time. Retire the existing rule before approving its replacement.
- The calculation service matches an approved event to an approved rule by exact category, event code, and severity. This allows different event types of the same severity to use different point values. Correction events are deliberately excluded from automatic scoring; they require a traceable correction workflow.
- The driver must already have a non-null `calculated_score`. The service does not invent the 80-point baseline from missing history. Baseline assignment still depends on the agreed verification/history eligibility policy.
- Applied changes are clamped to 0–100. The calculated score changes; a manual override remains separate and continues to determine the effective/display score when present.
- `PerformanceEventScoreApplication` records the rule, rule-name snapshot, points, previous/new calculated score, reason, and application time. Its one-to-one event relation prevents the same event from being scored twice through this service. A corresponding `ScoreHistory` row records the transition and actor.
- If the event has no matching approved rule or the driver has no established calculated score, the service returns without changing the score. An Admin can configure a rule later, and the approved event can then be explicitly processed by the scoring service.
- If the resulting effective score is below 40, the scoring service asks the availability workflow to place a low-score restriction when an Operations actor is supplied. Score increases and manual overrides never release existing restrictions automatically.
- Successful appeal corrections are handled by the Admin-only `correct_score_after_upheld_appeal` service. The recalculation excludes the overturned event while retaining original application records, adds a correction audit record, and never automatically releases restrictions or clears manual overrides.

### Prepared tests

- Model-definition tests cover the score range intent, event categories, effective-score selection, and signed history delta.
- Service tests cover Admin override history creation, preservation of the calculated score, Operator denial, and score/reason validation. Baseline tests cover Admin-only establishment, required verification/history confirmations, the unresolved no-history case, and prevention of duplicate baselines. Scoring-engine tests cover inactive proposals, Admin-only rule management, sign validation, one-time event application, score clamping, and withholding score changes when the calculated score is unset. Correction tests cover removing an overturned event from recalculation, replaying later valid events, preserving original applications, and retaining manual overrides/restrictions. Event-review tests cover Operator review, evidence requests, and prevention of silent final-decision replacement. Appeal/availability tests cover driver-only appeal submission, pending-appeal invariants, successful appeal audit, duplicate appeals, the strict below-40 threshold, Admin-only low-score restoration, critical-incident review restrictions, and release history.
- These tests have been committed but have **not** been executed in a local Django environment.



### Initial REST API layer

The following routes are registered under `/api/v1/performance/` and use authenticated profile/capability permissions:

- `GET/POST events/`: Operations users with the performance capability can list and submit event reports.
- `POST events/<event_id>/review/`: Operations users can approve, reject, or request more evidence, with a required reason.
- `GET/POST rules/`: list and propose scoring rules. The service layer restricts rule management to Admins.
- `POST rules/<rule_id>/<approve|retire>/`: approve or retire a proposed/active rule; Admin-only service checks still apply.
- `GET driver/me/`: a driver can inspect their own score, recent score history, and active performance restrictions.
- `GET driver/appeals/` and `POST driver/events/<event_id>/appeal/`: drivers can list their own appeals and appeal their own final event decisions.
- `POST appeals/<appeal_id>/review/`: authorized Operations users can decide pending appeals.
- `POST appeals/<appeal_id>/correct-score/`: Admin-only service applies an upheld-appeal correction with an audit reason.
- `POST scores/<score_id>/override/` and `GET scores/<score_id>/history/`: Admin score override and operations history inspection.

These endpoints have not been run against Django/DRF locally. A critical-incident restriction endpoint, explicit restriction-release endpoint, and baseline endpoint remain pending. The baseline endpoint is intentionally withheld until verification and history eligibility can be checked server-side rather than trusting booleans submitted by a client.

## Not implemented yet

- Runtime validation of hand-prepared migrations, verification of model loading, and local test execution. The Performance app is listed in Django settings.
- API integration tests and local runtime validation of event submission/review, serializer validation, and permission enforcement.
- A baseline API endpoint; exact point values remain unapproved and no rules are active by default. The baseline service exists, but eligibility confirmations must be derived from server-side Verification/history records before an endpoint is exposed.
- API integration tests for Admin score overrides, scoring-rule lifecycle, appeals, and score corrections.
- Runtime validation of migrations 0001–0005 and local execution of all tests. Integration with Verification and notification/availability wiring remain to be built.
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
