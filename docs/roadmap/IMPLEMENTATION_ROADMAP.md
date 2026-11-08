# DIVS Implementation Roadmap

**Project:** Driver Identification and Verification System (DIVS)  
**Repository:** https://github.com/smartsmartzone01-create/divs  
**Working branch:** `development`  
**Document purpose:** Shared implementation map and progress reference.

> **Branch rule:** All planned implementation work must target `development`. Do not modify or merge into `main` unless the project owner explicitly approves it. DIVS is separate from Tunakuza.

## How to read this roadmap

Statuses describe the known project position when this document was created. They are not a substitute for checking the current code, deployment, or tests.

- **Implemented** — code or UI has previously been added; still verify it when integration or deployment matters.
- **In progress** — implementation exists but has outstanding audit, deployment, integration, or acceptance checks.
- **Needs verification** — work was previously reported as present, but its actual completeness has not been established.
- **Planned** — not yet implemented or not yet confirmed.
- **Decision required** — product, legal, security, or provider choice must be made before implementation.

A commit is not proof that a feature deploys, passes tests, or is production-ready. Track those separately.

---

# Phase 1 — Verification infrastructure

**Objective:** Build a secure, auditable verification workflow and evidence foundation before expanding user-facing upload functionality.

| Stage | Scope | Known status |
|---|---|---|
| **1A — Evidence data foundation** | Evidence metadata model, evidence event history, migration, serializers and initial tests | Implemented; tests not confirmed as run |
| **1B — Private evidence storage** | Cloudflare R2 integration, private upload/retrieval endpoints, file validation, upload throttling and storage configuration | In progress; code committed, audit/deployment/live R2 test outstanding |
| **1C — Evidence security hardening** | Authorization tests, quarantine/malware-scanning strategy, access audit, retention/deletion policy, orphan cleanup and safe file delivery | In progress; access audit, R2 orphan reconciliation, explicit-expiry deletion/legal hold and missing-object handling are coded. Malware scanning is deferred for development; a DEBUG-gated pending-file retrieval option is implemented for the development service only. CI test workflow currently fails before exposing any test steps; full test execution remains unverified. |
| **1D — Verification workflow integration** | Connect evidence to identity, driving-licence, traffic/police and accident checks; evidence review states, trusted API result records and reviewer actions | In progress; manual evidence review, expiry-aware accepted-evidence gating, trusted server-side government-result audit records, licence-class audit events, Admin-only approval/activation and Admin-only check reopening, expiry processing that invalidates unsupported manual checks, and revocation of approved verification after a definitive trusted adverse provider result are coded. Actual provider integration, expiry scheduling and acceptance verification remain outstanding |
| **1E — Verification API and permission acceptance tests** | Driver ownership, operator capabilities, Admin-only decisions, approval/rejection, reopening, expiry revocation and activation rules | In progress; acceptance tests have been added for Admin-only reopening, Operator denial, evidence supersession, expiry-driven invalidation, alternate valid evidence, dry-run safety, availability deactivation, trusted adverse-result revocation after approval, pre-approval adverse findings without automatic final rejection, licence-class invalidation and protection against unavailable/error outcomes revoking approval. Tests have not been run by the assistant |

### Phase 1 acceptance criteria

- Drivers can submit evidence only for their own eligible verification checks.
- Operations users can access evidence only with the required capability.
- Admin-only decisions remain protected from Operators.
- Evidence objects remain private; there are no public object URLs.
- File type is determined from content, not trusted from the submitted filename or MIME header.
- Access and review actions are auditable.
- Production must remain fail-closed until a trusted scanner records a clean result. Development may explicitly allow pending evidence retrieval only when both `DEBUG=True` and `DIVS_ALLOW_UNSCANNED_EVIDENCE_ACCESS=true`; infected/error states remain blocked.
- Retention deletion requires an explicit expiry timestamp, an expired evidence status and no legal hold; evidence metadata and audit history remain.
- No statutory retention duration has been assumed. Recovery behavior and operational restore tests remain outstanding.
- A driver becomes publicly discoverable only after verification approval and separate Admin activation.
- Expired accepted evidence must stop supporting a manual check. If no other valid accepted evidence remains, invalidate the check, return approved verification to review, and deactivate active public availability.
- Evidence expiry processing and private-file retention deletion are separate operations; expiry processing must run before retention deletion.
- Government API result validity periods are not assumed; define them with the authorized source/provider policy before adding automatic API-result expiry.
- A definitive `NOT_MATCHED` result from the trusted server-side provider adapter can reopen an approved verification, invalidate the affected passed check, mark verified licence classes non-current when applicable, deactivate active availability and notify the driver. The evidence and provider-attempt history are preserved.
- `UNAVAILABLE`, `ERROR`, `INCONCLUSIVE` and later positive results cannot reopen an approved verification; final-result handling remains locked except for a definitive adverse provider result. No public endpoint accepts arbitrary provider outcomes.

### Stage 1C — current work sequence

1. Malware scanning is deferred for development. Keep the scanner adapter provider-neutral and production retrieval fail-closed.
2. Validate retention cleanup with explicit expiry and legal-hold safeguards; do not invent a retention duration.
3. Complete recovery validation for missing objects, orphan reconciliation and restore procedures.
4. Resolve GitHub Actions runner/workflow startup failure and execute the full backend suite.
5. Confirm the latest Render deployment is live and verify all expected migrations.
6. Complete Stage 1D by validating evidence-to-check binding, accepted-evidence expiry and scan-state gating, trusted API result recording, licence-class audit history and the manual fallback path.
7. Run `python manage.py process_expired_verification_evidence` as a dry run; execute only after reviewing the counts with `--execute`. Configure a scheduled run after the command is validated.

### Stage 1B — immediate work sequence

1. Audit the current `development` implementation before trusting it.
2. Verify the latest Render development deployment and inspect any build/runtime errors.
3. Run the relevant backend tests in an environment where they can actually execute; report only tests that were run.
4. Test a real upload to the private R2 bucket using a non-sensitive test document.
5. Test authorized retrieval and unauthorized access denial for both driver and operations routes.
6. Test failure behavior and check for orphaned R2 objects or incomplete database records.
7. Only after the backend path is verified, build the frontend evidence-upload experience.

**Known Stage 1B endpoints added in the implementation:**

- `POST verification/driver/checks/<check_id>/evidence/`
- `POST verification/operations/checks/<check_id>/evidence/`
- `GET verification/driver/evidence/<evidence_id>/file/`
- `GET verification/operations/evidence/<evidence_id>/file/`

Confirm the current URL configuration and permissions during the Stage 1B audit; this list records the intended endpoints, not a claim that they are live and working.

---

# Phase 2 — Driver registration and onboarding

**Objective:** Allow a driver to register, create a profile, submit a verification application and follow its progress.

| Stage | Scope | Known status |
|---|---|---|
| **2A — Registration interface** | Step-by-step driver onboarding form, validation and progress feedback | Previously implemented / needs verification |
| **2B — Registration API integration** | Submit registration data and create the correct driver profile | Needs verification |
| **2C — Verification application submission** | Submit the driver's verification application and required checks | Planned / needs verification |
| **2D — Driver verification status** | Show application status, check progress and outstanding requirements | Planned |
| **2E — Driver notifications** | Notify on submission, review, additional-information requests, approval and rejection | Planned / integrate existing notification service |

### Driver registration rules

- Driver, client and operations registration remain separate.
- Driver profile creation does not automatically make a driver searchable.
- Driver information includes full name, nationality, current residential place, region/district, experience, phone and optional email.
- Date of birth is deferred until national identity verification.
- A name or date-of-birth mismatch against verified identity information must be flagged for review rather than silently overwritten.
- Driver visibility requires verification approval and Admin activation.

---

# Phase 3 — Driver Workspace

**Objective:** Give drivers a clear, phone-first workspace for managing their profile and understanding their verification and performance.

The Driver Workspace is the visual reference for the Client and Admin workspaces.

| Stage | Scope | Known status |
|---|---|---|
| **3A — Workspace dashboard** | Driver home, status summary, navigation and responsive layout | Needs verification |
| **3B — Profile overview and editing** | Profile details, editable fields and change handling | Planned |
| **3C — Verification dashboard** | Check statuses, evidence submission and review feedback | Planned |
| **3D — Performance dashboard** | Score, indicators, history and reasons | Planned |
| **3E — Appeals and restrictions** | View restrictions and submit eligible appeals | Planned |
| **3F — Notifications and settings** | Notifications, account settings and workspace navigation | Planned |

### UI/UX standards

- Professional, simple and phone-first.
- Readable text and cards that do not overflow.
- Clear visual distinction between normal, success, warning and error states.
- Dark mode, light mode and Swahili support.
- Avoid unnecessary complexity and unexpected navigation.
- Preserve the established Driver Workspace visual language across all workspaces.

---

# Phase 4 — Operations and Admin Workspaces

**Objective:** Provide internal tools while strictly preserving the separation between Operator and Admin authority.

| Stage | Scope | Known status |
|---|---|---|
| **4A — Roles and capabilities** | Operations roles, permission checks and capability enforcement | Previously implemented; needs acceptance verification |
| **4B — Verification queue and detail UI** | Admin/operations verification queue and detail pages | Previously implemented; mobile reported working |
| **4C — Review tools** | Record findings for identity, licence, traffic and accident checks; manage check evidence | Partially implemented / needs verification |
| **4D — Final verification decisions** | Approval, Admin-only rejection, separate Admin availability activation | Backend workflow previously implemented / needs verification |
| **4E — Driver registration management** | Review and manage driver registration applications | Planned |
| **4F — Appeals and invitations** | Appeal decisions, invitation management and administrative actions | Planned |
| **4G — Audit and activity history** | Record who performed each action, when and why; notify affected users | Planned / integrate existing services |

### Authority boundaries

**Operator may:**
- View the operations workspace.
- Manage driver registrations.
- Review verification information and evidence.
- Accept or reject submitted evidence with an auditable review decision.
- Record preliminary findings for the four verification checks.
- Manage driver performance where authorized.

**Operator may not:**
- Approve or reject final verification.
- Activate public driver availability.
- Remove drivers.
- Approve appeals or reserved administrative decisions.
- Manage Admin invitations unless explicitly granted by a future policy.

**Admin may additionally:**
- Approve or reject final verification.
- Activate or deactivate driver availability.
- Manage restrictions and suspensions.
- Remove drivers.
- Approve appeals.
- Manage invitations and reserved administrative decisions.

Admin registration is not public. Admin access is controlled through the established approval/invitation process. An applicant must never approve their own administrative access.

### Verification decision rules

- Findings do not automatically decide the overall verification outcome.
- Final approval/rejection is an explicit Admin-only decision.
- Approval and public availability activation are separate actions.
- Reopening a check or revoking approval is Admin-only.
- Reopening must remove the driver from discovery, preserve previous findings/history, set the verification back to review and notify the driver.
- Reapproval does not automatically reactivate public availability; Admin activation is still required.
- Ordinary profile edits must not automatically unpublish a driver. Only changes to critical verification information or checks should trigger the defined review rules.

---

# Phase 5 — Client registration and workspace

**Objective:** Allow individuals and companies to register and manage their driver-search and engagement activity.

| Stage | Scope | Known status |
|---|---|---|
| **5A — Client registration** | Client registration interface and API | Planned |
| **5B — Client profile** | Client profile and account management | Planned |
| **5C — Client workspace** | Client dashboard using the Driver Workspace design standards | Planned |
| **5D — Engagement history and notifications** | Track which client engaged which driver and related notifications | Planned |

Client registration does not require the driver verification process. Client and company details must still be handled with appropriate privacy and access controls.

---

# Phase 6 — Public driver discovery

**Objective:** Let the public browse and search eligible verified drivers without requiring an account.

| Stage | Scope | Known status |
|---|---|---|
| **6A — Public listing and search** | Public driver listing and search interface | Planned |
| **6B — Location and experience filters** | Region, district, residential area and experience | Planned |
| **6C — Verified qualifications filters** | Verified licence classes and qualifications | Planned |
| **6D — Performance and availability filters** | Performance ranking and availability | Planned |
| **6E — Public driver profile** | Public profile and clear verification indicators | Planned |
| **6F — Protected contact access** | Restrict direct contact information until the client satisfies payment and authorization rules | Planned |

### Discovery rules

- Public browsing does not require login.
- Only verified and Admin-activated drivers are discoverable.
- Verified licence information is the source of truth for licence-class filtering.
- Ranking should favor trustworthy, evidence-backed performance rather than unverified claims.
- Driver contact information remains protected until the agreed client access conditions are met.

---

# Phase 7 — Performance and engagement system

**Objective:** Build a transparent, traceable system for driver performance and client engagement.

| Stage | Scope | Known status |
|---|---|---|
| **7A — Performance event model** | Define event types, scoring rules and authorized sources | Planned |
| **7B — Performance records** | Record positive and negative events with reasons and supporting context | Planned |
| **7C — Score history** | Preserve score changes, timestamps and explanations | Planned |
| **7D — Client engagement records** | Track which client contacted, hired or engaged which driver | Planned |
| **7E — Disputes and appeals** | Allow eligible performance records to be challenged and reviewed | Planned |

Scoring rules must be explainable, consistent and resistant to manipulation. A score should never change without a traceable event and reason.

---

# Phase 8 — Payments and commercial access

**Objective:** Implement controlled paid access to protected driver contact information.

| Stage | Scope | Known status |
|---|---|---|
| **8A — Payment provider decision** | Select a provider suitable for the intended markets and currencies | Decision required |
| **8B — Payment integration** | Process client payments and record transactions | Planned |
| **8C — Contact release** | Release protected contact details only after verified payment and authorization | Planned |
| **8D — Payment lifecycle** | Handle success, failure, duplicate callbacks, refunds and reconciliation | Planned |
| **8E — Admin payment tools** | Payment monitoring and reporting | Planned |

Payment confirmation must be verified server-side. A frontend success message alone must never grant contact access.

---

# Phase 9 — Government and external verification integrations

**Objective:** Integrate authoritative sources when access, legal authority and technical agreements are available.

| Stage | Scope | Known status |
|---|---|---|
| **9A — Integration architecture** | Define provider adapters, credentials, audit and failure handling | Planned |
| **9B — National identity checks** | Verify identity through an authorized source | Planned |
| **9C — Driving licence checks** | Verify licence validity and classes | Planned |
| **9D — Traffic/police checks** | Integrate authorized traffic or police record checks | Planned |
| **9E — Accident record checks** | Integrate authorized accident record checks | Planned |
| **9F — Manual fallback** | Maintain reviewed manual workflows when APIs are unavailable | Planned |

### Data protection principle

Do not store raw government identity data, raw licence data, police records or raw API payloads unnecessarily. Retain only the minimum verification outcome, references and audit details required for the lawful operation of DIVS. Confirm legal authority, consent, access terms and retention obligations before connecting any government source.

---

# Phase 10 — Production readiness and launch

**Objective:** Verify the whole system is secure, reliable, recoverable and operationally ready.

| Stage | Scope | Known status |
|---|---|---|
| **10A — Security and permissions audit** | Authentication, authorization, sensitive data, file access and abuse controls | Planned |
| **10B — End-to-end testing** | Frontend/backend integration and complete user journeys | Planned |
| **10C — Backup and recovery** | Database backups, restore tests and evidence-object recovery | Planned |
| **10D — Monitoring and observability** | Service health, logs, errors and operational alerts | Partially available / needs verification |
| **10E — Privacy and operational policies** | Retention, deletion, access, incident and support procedures | Planned |
| **10F — Performance and security testing** | Load, resilience, dependency and security testing | Planned |
| **10G — Production deployment and launch** | Production environment, release checks and launch | Planned |

---

# Shared implementation rules

1. Work on the `development` branch only unless the project owner explicitly approves otherwise.
2. Keep `main` untouched.
3. Keep DIVS separate from Tunakuza.
4. Before code changes, state the exact files expected to change and the purpose of each.
5. Make small, focused commits.
6. After a commit, report the exact changed files and actual commit SHA.
7. Do not claim tests, builds, deployments or live integrations succeeded unless they were actually executed and verified.
8. Prefer step-by-step instructions that work with GitHub, Render and Cloudflare dashboards; do not assume shell access is available.
9. Protect secrets. Never request or commit API keys, passwords, access tokens or private credentials.
10. Treat implementation, deployment, testing and production readiness as separate checkpoints.
11. Preserve the established role boundaries, privacy rules and Driver Workspace UI/UX standards.
12. Do not introduce a new provider, retention period, payment rule or legal assumption without an explicit decision.

# How to resume work

Use the stage identifiers in conversations and GitHub issues:

- `Continue 1B` — audit and finish the private R2 evidence-storage foundation.
- `Review 1B` — inspect current code and deployment before changing anything.
- `Continue 1C` — complete recovery validation and security acceptance tests; malware scanning remains deferred for development.
- `Start 1D` — connect evidence acceptance to the four verification checks and review workflow.
- `Continue 2A` — review or continue driver onboarding.
- `Review Phase 4` — inspect Operations/Admin workflow and permission boundaries.
- `Revise Phase 6` — revisit public discovery requirements.

**Recommended next step:** Resolve the GitHub Actions runner startup failure, run the backend suite, verify the latest Render deployment and complete Stage 1C recovery acceptance before moving to Stage 1D.
