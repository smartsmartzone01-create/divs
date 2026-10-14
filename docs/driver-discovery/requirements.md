# DIVS Driver Discovery & Filtering — Requirements

**Status:** Agreed product rules; implementation pending  
**Branch:** `development`

## Public discovery

- Public driver discovery and filtering are available without signing in.
- Authentication is required when a person wants to contact or hire a driver, register as a driver, or access an authorized Operations workspace.
- Public discovery must never expose private contact details, licence documents, identity numbers, raw government responses, or sensitive verification evidence.
- Driver discovery must use existing registration, profile, verification, performance, and availability records. Do not create duplicate driver identities or verification workflows.

## Eligibility before ranking

A driver is shown as available for hire only when all required conditions are satisfied:

1. The driver profile is active.
2. The overall driver verification is approved and all required verification checks have passed.
3. The driver has no active performance-based availability restriction.
4. The driver meets any selected search filters.

Verification, profile lifecycle, performance review, and availability are separate decisions. Passing one does not automatically satisfy the others.

## Licence verification is authoritative

- DIVS does not accept a licence class entered during general registration as a verified qualification.
- The driver must present a driving licence and its information must be validated through an approved verification method before the licence details qualify the driver for discovery or employment.
- Verified licence-class information is authoritative for licence-related qualifications. If registered licence information conflicts with validated licence information, the validated information takes precedence.
- Licence-class filters use only validated licence-class records. Unverified, pending, failed, inconclusive, or review-needed licence information must not qualify a driver for a class.
- Extend the existing Verification module and associate verified licence-class details with its existing verification records. Do not create a parallel verification status or workflow.
- Store only the minimum structured licence information needed for eligibility and filtering. Do not store raw government API payloads or expose licence evidence, licence numbers, or documents in public results.

## Location is separate from licence information

- Licence verification does not determine or override residential location.
- Location filtering uses the driver's residential-location data, not licence data.
- A structured residential-area field is a proposed data-model improvement because the current registration model has region, district, and a free-text residential address. It remains subject to product approval before implementation.
- Do not infer a driver's residential area from their licence or licence-verification result.

## Search filters

The initial public filters are:

1. **Location:** region, district, and residential area when structured data is available.
2. **Driving experience:** use the existing registration experience categories; these are categories, not exact years.
3. **Verified licence class:** use validated licence information only.
4. **Performance score:** use the effective score (manual Admin override when present, otherwise calculated score).
5. **Availability:** only eligible drivers without active restrictions can be presented as available for hire.

## Ranking

- Apply eligibility checks first, then search filters, then ranking.
- Rank eligible matching drivers by effective performance score, highest first.
- A missing/unestablished score is not zero and must not be treated as poor performance. Drivers without a score may appear if otherwise eligible, but should not outrank drivers with established higher scores solely because their score is missing.
- Use a stable, documented tie-breaker if effective scores are equal.
- An Admin score override affects the effective score and ranking, while the calculated score and its history remain preserved.

## Safe public result fields

Public result summaries may include a safe display name, residential location, registered experience category, validated licence classes, effective score when established, and hire availability. They must not include private contact information, licence numbers, uploaded licence documents, identity numbers, or sensitive verification evidence.

## Existing model dependencies inspected

- `DriverRegistration` currently has region, district, free-text `current_residential_address`, and fixed `driving_experience` choices; it has no structured residential-area field.
- `DriverProfile` is the existing profile identity and should remain the discovery anchor.
- `DriverVerification` and `DriverVerificationCheck` already record overall status and minimal outcomes for the driving-licence check, but do not currently store structured validated licence classes.
- `DriverScore.effective_score` is the score source for ranking.
- Existing performance restrictions are a separate input to hire availability.

## Next implementation steps

1. Add the structured validated licence-class representation within the existing Verification module, with eligibility tied to a passed/approved licence validation.
2. Confirm and then add structured residential-area data without removing the existing address field.
3. Implement discovery eligibility, filters, ranking, and safe public serializers using existing profile, verification, performance, and availability records.
4. Add tests for public access, licence-validation gating, location filtering, missing scores, ranking, restrictions, and private-data exclusion.

Runtime validation remains pending until the project is run in a local Django environment.
