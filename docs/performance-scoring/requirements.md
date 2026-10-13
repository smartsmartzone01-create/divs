# DIVS Performance & Scoring — Requirements and Agreed Rules

**Status:** Workflow agreed; implementation in progress.  
**Target app:** `backend/apps/performance/`  
**Branch:** `development`  
**Purpose:** Define the product rules before creating the Performance & Scoring app. This document records agreed decisions and distinguishes them from proposed point values that still need final approval.

## 1. Responsibilities and boundaries

The Performance & Scoring app owns:
- Performance event records and evidence references.
- Event review decisions and appeals.
- Scoring rules, score calculation, score overrides, and score history.
- Performance-related availability restrictions and restoration decisions.
- Audit records for actions performed within these workflows.

It must integrate with existing DIVS Identity, Profiles, Verification, Operations, and Notifications apps. It must not duplicate account, profile, operations membership, or notification systems.

## 2. Starting score and score limits

- Score range: **0–100**.
- Agreed baseline: **80/100 for a driver who has been verified and whose applicable history has been verified/reviewed**.
- Positive and negative approved performance events can raise or lower the score.
- The score must never go below 0 or above 100.
- Identity/licence verification and performance history are different concepts and must be displayed separately.
- Do not treat a lack of performance records as proof of poor performance.
- The exact handling and display label for drivers with no verified performance history must be confirmed before implementation if it affects whether the 80-point baseline can be assigned.

## 3. Performance event categories

Three event categories are agreed:
1. **Positive** — evidence-backed good performance.
2. **Negative** — evidence-backed performance concerns or incidents.
3. **Correction** — a documented correction to an earlier event or score outcome.

Initial examples (examples only; event eligibility and points require approved rules):
- Positive: confirmed on-time delivery, substantiated excellent client feedback, reliable service across completed jobs, confirmed safe-driving record over a defined review period.
- Negative: confirmed minor/serious traffic violation, unjustified late delivery, substantiated misconduct, preventable accident where responsibility is established, dangerous driving.
- Correction: correct inaccurate event information or reverse/adjust an earlier decision following review or appeal.

An allegation is not a confirmed negative event. The same incident must not cause duplicate deductions.

## 4. Severity levels

Severity categories are agreed as **Minor**, **Serious**, and **Critical**.

Proposed point ranges discussed (not final event-by-event values):
- Minor: approximately **−1 to −3**.
- Serious: approximately **−5 to −15**.
- Critical: approximately **−15 to −30**.

Severity must be based on established facts and incident impact, not merely on the existence of an accident report. An accident record alone does not establish fault. Exact categories, thresholds, and points must be configurable through approved scoring rules.

## 5. Review workflow

1. An event is received through an authorized manual entry, uploaded/supporting evidence, or a connected trusted source.
2. The system performs available automatic checks, such as source validation, required-field checks, duplicate detection, and conflict/uncertainty detection.
3. The event enters the appropriate review path:
   - Manual Operations review.
   - Automatic validation when a trusted integration and approved rule can determine the outcome reliably.
   - Combined review, with uncertain or conflicting cases referred to Operations.
4. The reviewer records a decision: **approve**, **reject**, or **request more evidence / further review**.
5. Only an approved event can change the score.
6. The system applies any approved score effect, evaluates availability restrictions, and records a complete history.
7. The driver and relevant Operations users receive appropriate notifications.

Automatic review must not imply that an unverified allegation is proven. Government-source checks should use authorized integrations. Store only the minimum permitted outcome and event metadata; do not copy sensitive government records into DIVS unnecessarily.

## 6. Roles and permissions

- **Admins and Operators:** Both may review performance events and verify drivers within their authorized operational responsibilities.
- **Admins and Operators:** Both may carry out manual evidence review and act on reliable automatic-review results.
- **Scoring-rule changes:** Admin approval is required before a proposed rule change becomes active. A proposed or edited rule must not affect scoring until approved.
- **Admin score override:** Admins may manually override the automatically calculated score. Operators do not receive this override authority by this agreement.
- **Operator audit:** Admins can inspect operator activity.
- **Operator access revocation:** Only Admins can revoke an Operator's access.
- **Initial system superuser and other Operations permissions:** Continue to follow the existing DIVS Operations authorization model; this document adds Performance & Scoring requirements and does not grant permissions merely by documenting them.

Permission checks must be enforced in backend endpoints/services, not only hidden in the user interface.

## 7. Manual score override and audit

An Admin may override the calculated score when justified. Each override must record at least:
- Driver and score record.
- Previous score and new score.
- Point difference.
- Required reason/justification.
- Admin account that made the change.
- Timestamp.
- Whether the score is currently system-calculated or manually overridden.
- Any applicable review/reference record.

An override must not erase or rewrite underlying performance events or previous score history. The system must preserve the event-derived score history and the separate override action so later reviewers can understand why the displayed score differs from the automatic calculation.

A manual override cannot bypass availability restrictions. In particular, setting a higher score must not by itself remove a critical-incident restriction or a low-score restriction. The applicable authorized restoration decision must still be recorded.

## 8. Availability restrictions

### Critical incident
- A credible critical incident triggers immediate **Under Review** status and a temporary restriction from being presented as available for hire while investigated.
- This precaution is not a finding that the driver is at fault.
- Operations investigates and records the outcome. Availability restoration follows the authorized decision process and applicable DIVS policy.

### Low score
- A score **below 40/100** triggers a restriction from being presented as available for hire.
- A score of exactly **40** does not trigger this low-score restriction.
- The case requires review.
- Only an Admin can approve restoration of availability after a low-score restriction.
- A score override alone does not restore availability.

Restrictions should be represented explicitly, with reason, status, timestamps, and decision history. Do not conflate profile lifecycle status, driver verification status, performance review status, and availability eligibility.

## 9. Appeals and corrections

- Drivers may challenge a performance event or its outcome through an appeal/correction workflow.
- While an appeal is pending, the current score and existing restrictions remain in effect.
- If the appeal succeeds, record the decision and make the appropriate score correction.
- Never delete the original event, original decision, or previous score history. Record the correction as a new traceable action.
- Appeals must be decided by an authorized reviewer; the applicable role and escalation policy should be enforced by backend permissions.
- Duplicate reports of the same incident must not cause duplicate score deductions.

## 10. Score history and reasons

Every score change must be traceable and show, at minimum:
- Previous score, new score, and change amount.
- Related event/rule or manual override reference.
- Reason for the change.
- Decision/review status.
- Actor or system process responsible.
- Timestamp.
- Relevant correction or appeal link, where applicable.

Historical entries must be append-only from the normal workflow. Corrections are represented as additional history, not silent edits.

## 11. Initial event point proposals

The following figures were discussed as starting proposals only and are **not yet approved as final scoring rules**:

### Positive examples
- Confirmed on-time delivery: +1.
- Substantiated excellent client feedback: +2.
- Confirmed safe-driving record over a defined review period: +3.
- Reliable service across multiple completed jobs: +3.

### Negative examples
- Confirmed minor traffic violation: −3.
- Confirmed late delivery without a valid reason: −2.
- Substantiated client misconduct complaint: −3.
- Confirmed serious traffic violation: −10.
- Confirmed preventable accident: −10, only where responsibility is established.
- Confirmed serious misconduct or dangerous driving: −15.

These individual event values must be reviewed against the approved severity framework before being made active. The severity ranges above and the example values may overlap; implementation must use a single approved rule for a given event and prevent duplicate penalties.

## 12. Integration requirements

- **Identity:** Attribute user actions to the correct account.
- **Profiles:** Link events and scores to the driver's existing profile; do not create a duplicate driver identity.
- **Verification:** Use verification outcomes as context where appropriate, but keep verification status separate from performance score.
- **Operations:** Use the existing Operations roles/capabilities and enforce the agreed Admin/Operator permissions.
- **Notifications:** Notify drivers and relevant Operations users of material decisions, score changes, appeals, critical review status, and availability restrictions.
- **Discovery/availability:** Ensure restricted drivers are not presented as available for hire. Public discovery ranking remains a separate concern from the score itself.
- **Government integrations:** Build adapters only when the authorized API contract and access are available; uncertain or conflicting data must be escalated for review.

## 13. Proposed app organization

Create `backend/apps/performance/` as a dedicated Django app with clear internal responsibilities:
- Events and evidence references.
- Reviews and appeals.
- Scoring rules, calculation, and score history.
- Availability restrictions.
- Services, serializers, views/API, URLs, permissions, and tests as appropriate to the existing DIVS conventions.

Keep the first implementation incremental and integrate with existing modules rather than rebuilding their responsibilities.

## 14. Development and documentation commitments

- Develop on `development`; leave `main` untouched unless the user explicitly approves a merge.
- Keep changes small and report the changed files and commit.
- Tests and migrations may be added with implementation, but the user will run them locally later. Do not claim they have been run.
- Maintain a separate technical document during coding describing the implemented performance rules, score calculation, event/review lifecycle, permissions, audit behavior, and availability restrictions. Update that document as behavior is implemented.
- This requirements document captures agreed product rules and unresolved details; the technical document must describe actual implemented behavior and clearly identify anything not implemented yet.
