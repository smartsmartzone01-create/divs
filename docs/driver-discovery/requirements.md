# DIVS Driver Discovery & Filtering — Requirements

**Status:** Initial implementation committed; runtime validation pending  
**Branch:** `development`

## Public discovery

- Public driver discovery and filtering are available without signing in.
- Authentication is required when a person wants to contact or hire a driver, register as a driver, or access an authorized Operations workspace.
- Public discovery must never expose private contact details, licence documents, identity numbers, raw government responses, or sensitive verification evidence.
- Driver discovery uses existing registration, profile, verification, performance, and availability records. It does not create duplicate driver identities or verification workflows.
- Initial public endpoint: `GET /api/v1/discovery/drivers/`.
- This endpoint implements public discovery only. Driver contact, paid contact unlock, hiring requests, and payment processing are separate flows and are not implemented by this endpoint.
- In this response, `availability: "available"` means eligible to appear in the hiring directory under the rules below; it does not guarantee the driver has an open schedule or has accepted a job.

## Eligibility before ranking

A driver is shown as available for hire only when all required conditions are satisfied:

1. The driver profile is active.
2. The overall driver verification is approved and all required verification checks have passed.
3. The driving-licence check specifically passed with result `valid` and at least one current verified licence class is recorded.
4. The driver has no active performance-based availability restriction.
5. If an effective performance score exists, it must be at least 40. A score below 40 excludes the driver from public hiring results even if a restriction record is missing; a score of exactly 40 is not excluded by this threshold.
6. The driver meets any selected search filters.

Verification, profile lifecycle, performance review, and availability are separate decisions. Passing one does not automatically satisfy the others.

## Licence verification is authoritative

- DIVS does not accept a licence class entered during general registration as a verified qualification. Driver registration currently has no licence-class field.
- The driver must present a driving licence and its information must be validated through an approved verification method before licence details qualify the driver for discovery or employment.
- Verified licence-class information is authoritative for licence-related qualifications. If any future registered licence information conflicts with validated licence information, the validated information takes precedence.
- Licence-class filters use only current class records attached to a driving-licence check whose status is `passed` and result is `valid`.
- Verified classes are recorded through the existing Verification module after the licence check passes. A new class list does not create a second verification workflow or duplicate overall status.
- When classes are updated, previous class records are retained but marked non-current. If the underlying check is no longer passed and valid, its classes do not qualify for discovery.
- Store only the minimum structured licence information needed for eligibility and filtering. Do not store raw government API payloads or expose licence evidence, licence numbers, or documents in public results.

Operations endpoint for validated classes: `POST /api/v1/verification/operations/checks/<check_id>/licence-classes/` with `{"licence_classes": ["C", "CE"]}`. The referenced check must already be a passed driving-licence check with result `valid`; values are normalized to uppercase alphanumeric class codes.

## Location is separate from licence information

- Licence verification does not determine or override residential location.
- Location filtering uses the driver's residential-location data, not licence data.
- `DriverRegistration` now includes an optional structured `residential_area` field while retaining `current_residential_address`.
- Existing registrations can leave `residential_area` blank until that information is provided. Discovery does not infer a residential area from a full address or licence.

## Search filters

The initial public endpoint supports:

- `region`, `district`, and `residential_area` (case-insensitive partial matching)
- `experience` (exact existing registration category)
- `licence_class` (case-insensitive exact match against validated classes)
- `min_score` and `max_score` (integers from 0 to 100, using effective score)
- `limit` (1–100; defaults to 25)

Only eligible, unrestricted drivers are returned, so returned drivers are marked `available`. The label means eligible for the directory, not a real-time schedule confirmation.

## Ranking

- Apply eligibility checks first, then search filters, then ranking.
- Rank eligible matching drivers by effective performance score, highest first; the current profile update timestamp is the tie-breaker.
- A missing/unestablished score is not zero and must not be treated as poor performance. Drivers without a score may appear if otherwise eligible, but any driver with an established score ranks ahead of unscored drivers.
- An Admin score override affects the effective score and ranking, while the calculated score and its history remain preserved.

## Safe public result fields

Public result summaries include a display name, region, district, residential area, registered experience category, validated licence classes, effective score when established, and availability. They exclude private contact details, the full residential address, licence numbers, uploaded licence documents, identity numbers, and sensitive verification evidence.

## Existing model dependencies

- `DriverRegistration` supplies location and fixed `driving_experience` categories.
- `DriverProfile` remains the existing discovery identity.
- `DriverVerification` and `DriverVerificationCheck` supply the verification state; `VerifiedDriverLicenceClass` stores minimal validated class details associated with the existing driving-licence check.
- `DriverScore.effective_score` supplies the ranking score.
- Active `AvailabilityRestriction` records exclude a driver from available-for-hire results.

## Validation status

Automated tests have been added or updated for verified-class gating, public access, filtering, ranking unscored drivers below scored drivers, active restriction exclusion, private-field exclusion, the strict score-40 boundary, invalid score filters, and score-filter behavior for unscored drivers. The discovery query and serializer now reuse prefetched verification/class relations to reduce per-driver database queries. These tests have **not** been executed in a local Django environment. Migration application, endpoint runtime behavior, query-count validation, and integration tests remain pending.
