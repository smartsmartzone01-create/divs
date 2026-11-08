"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { WorkspaceHeader } from "@/components/workspace/workspace-header";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";
import { apiRequest, ApiError } from "@/lib/api/client";

type Check = {
  id: string; check_type: string; status: string; method: string; result_code: string;
  review_notes: string; checked_at: string | null;
  verified_licence_classes: { id: string; licence_class: string; is_current: boolean; verified_at: string }[];
};
type Event = { id: string; event_type: string; previous_status: string; new_status: string; notes: string; created_at: string; };
type Registration = {
  first_name: string; middle_name: string; last_name: string; nationality: string;
  region: string; district: string; residential_area: string; current_residential_address: string;
  driving_experience: string; contact_email: string | null; contact_phone_number: string | null;
};
type Verification = {
  id: string; status: string; profile_status: string; is_discoverable: boolean;
  decision_reason: string; decided_at: string | null; checks: Check[]; events: Event[];
  registration: Registration; created_at: string;
};
type Access = { role: "admin" | "operator"; capabilities: string[] };
type ResultOption = { value: string; en: string; sw: string };
const checkMeta: Record<string, { en: string; sw: string; results: ResultOption[] }> = {
  national_identity: { en: "Identity", sw: "Utambulisho", results: [
    { value: "match", en: "Details match", sw: "Taarifa zinalingana" }, { value: "mismatch", en: "Details do not match", sw: "Taarifa hazilingani" }, { value: "inconclusive", en: "Inconclusive", sw: "Haijathibitishwa" },
  ]},
  driving_licence: { en: "Driving licence", sw: "Leseni ya udereva", results: [
    { value: "valid", en: "Valid", sw: "Halali" }, { value: "invalid", en: "Invalid", sw: "Si halali" }, { value: "inconclusive", en: "Inconclusive", sw: "Haijathibitishwa" },
  ]},
  traffic_records: { en: "Traffic / police records", sw: "Rekodi za polisi/barabarani", results: [
    { value: "clear", en: "No disqualifying record", sw: "Hakuna rekodi inayozuia" }, { value: "record_found", en: "Record found", sw: "Rekodi imepatikana" }, { value: "inconclusive", en: "Inconclusive", sw: "Haijathibitishwa" },
  ]},
  accident_records: { en: "Accident records", sw: "Rekodi za ajali", results: [
    { value: "clear", en: "No disqualifying record", sw: "Hakuna rekodi inayozuia" }, { value: "record_found", en: "Record found", sw: "Rekodi imepatikana" }, { value: "inconclusive", en: "Inconclusive", sw: "Haijathibitishwa" },
  ]},
};
const passResult: Record<string, string> = { national_identity: "match", driving_licence: "valid", traffic_records: "clear", accident_records: "clear" };
function explainError(error: unknown, sw: boolean) {
  if (error instanceof ApiError) {
    const payload = error.payload as { detail?: string } | undefined;
    if (payload?.detail) return payload.detail;
    if (error.status === 403) return sw ? "Huna ruhusa ya kufanya kitendo hiki." : "You do not have permission to perform this action.";
  }
  return error instanceof Error ? error.message : (sw ? "Hitilafu imetokea." : "Something went wrong.");
}

export default function DriverVerificationDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  const [item, setItem] = useState<Verification | null>(null);
  const [access, setAccess] = useState<Access | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [decisionReason, setDecisionReason] = useState("");
  const [licenceInput, setLicenceInput] = useState("");
  const [draftResults, setDraftResults] = useState<Record<string, string>>({});
  const [draftNotes, setDraftNotes] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    const [detail, permissions] = await Promise.all([
      apiRequest<Verification>(`verification/operations/${id}/`),
      apiRequest<Access>("operations/me/"),
    ]);
    setItem(detail); setAccess(permissions);
  }, [id]);

  useEffect(() => {
    let active = true;
    Promise.all([
      apiRequest<Verification>(`verification/operations/${id}/`),
      apiRequest<Access>("operations/me/"),
    ]).then(([detail, permissions]) => {
      if (active) { setItem(detail); setAccess(permissions); }
    }).catch((caught) => { if (active) setError(explainError(caught, sw)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id, sw]);

  const canReview = !!access?.capabilities.includes("review_driver_verification");
  const canApprove = !!access?.capabilities.includes("approve_driver_verification");
  const canReject = !!access?.capabilities.includes("reject_driver_verification");
  const canActivate = !!access?.capabilities.includes("activate_driver_availability");
  const registration = item?.registration;
  const fullName = registration ? [registration.first_name, registration.middle_name, registration.last_name].filter(Boolean).join(" ") : "";
  const allPassed = !!item && item.checks.length === 4 && item.checks.every((check) => check.status === "passed" && check.result_code === passResult[check.check_type]);
  const licenceCheck = item?.checks.find((check) => check.check_type === "driving_licence");
  const hasCurrentLicenceClass = !!licenceCheck?.verified_licence_classes.some((entry) => entry.is_current);
  const finalDecisionMade = item?.status === "approved" || item?.status === "rejected";
  const sortedEvents = useMemo(() => [...(item?.events ?? [])].reverse(), [item?.events]);

  async function runAction(path: string, actionKey: string, success: string, body?: unknown) {
    setBusy(actionKey); setError(""); setNotice("");
    try { await apiRequest(path, { method: "POST", body: body ?? {} }); await load(); setNotice(success); }
    catch (caught) { setError(explainError(caught, sw)); }
    finally { setBusy(""); }
  }
  async function saveCheck(check: Check, resultCode: string, notes: string) {
    const status = resultCode === passResult[check.check_type] ? "passed" : resultCode === "inconclusive" ? "needs_review" : "failed";
    await runAction(`verification/operations/checks/${check.id}/review/`, "check-" + check.id,
      sw ? "Matokeo ya ukaguzi yamehifadhiwa." : "Review finding saved.",
      { status, result_code: resultCode, review_notes: notes });
  }
  async function saveLicenceClasses(check: Check) {
    const classes = licenceInput.split(",").map((value) => value.trim().toUpperCase()).filter(Boolean);
    if (!classes.length) { setError(sw ? "Weka angalau darasa moja la leseni." : "Enter at least one licence class."); return; }
    await runAction(`verification/operations/checks/${check.id}/licence-classes/`, "licence",
      sw ? "Madarasa ya leseni yamehifadhiwa." : "Verified licence classes saved.",
      { licence_classes: classes });
    setLicenceInput("");
  }

  return (
    <main className="workspace-shell admin-workspace verification-workspace">
      <WorkspaceHeader />
      <div className="verification-content">
        <Link href="/workspace/admin/verification" className="verification-back">← {sw ? "Orodha ya uhakiki" : "Verification queue"}</Link>
        {loading ? <div className="verification-empty">{sw ? "Inapakia taarifa za dereva…" : "Loading driver application…"}</div> :
          !item || !registration ? <div className="verification-empty"><strong>{sw ? "Maombi hayapatikani" : "Application unavailable"}</strong><p>{error || (sw ? "Maombi hayawezi kupatikana." : "This application could not be loaded.")}</p></div> :
          <>
            <header className="verification-page-heading">
              <p className="admin-eyebrow">{sw ? "TAARIFA ZA DEREVA" : "DRIVER APPLICATION"}</p>
              <h1>{fullName}</h1><p>{[registration.residential_area, registration.district, registration.region].filter(Boolean).join(", ")}</p>
              <div className="verification-heading-status"><span className={"verification-status status-" + item.status}>{item.status.replaceAll("_", " ")}</span><span className={"verification-status status-" + item.profile_status}>{item.profile_status.replaceAll("_", " ")}</span></div>
            </header>
            {error ? <p className="verification-alert" role="alert">{error}</p> : null}
            {notice ? <p className="verification-success" role="status">{notice}</p> : null}

            <section className="verification-panel">
              <div className="verification-panel-heading"><div><h2>{sw ? "Taarifa za usajili" : "Registration details"}</h2><p>{sw ? "Taarifa zilizowasilishwa na dereva." : "Information submitted by the driver."}</p></div></div>
              <div className="verification-detail-grid">
                <div><span>{sw ? "Jina kamili" : "Full name"}</span><strong>{fullName}</strong></div>
                <div><span>{sw ? "Uraia" : "Nationality"}</span><strong>{registration.nationality || "—"}</strong></div>
                <div><span>{sw ? "Simu" : "Phone"}</span><strong>{registration.contact_phone_number || "—"}</strong></div>
                <div><span>{sw ? "Barua pepe" : "Email"}</span><strong>{registration.contact_email || "—"}</strong></div>
                <div><span>{sw ? "Mkoa" : "Region"}</span><strong>{registration.region || "—"}</strong></div>
                <div><span>{sw ? "Wilaya" : "District"}</span><strong>{registration.district || "—"}</strong></div>
                <div><span>{sw ? "Eneo la makazi" : "Residential area"}</span><strong>{registration.residential_area || "—"}</strong></div>
                <div><span>{sw ? "Anwani ya sasa" : "Current address"}</span><strong>{registration.current_residential_address || "—"}</strong></div>
                <div><span>{sw ? "Uzoefu wa udereva" : "Driving experience"}</span><strong>{registration.driving_experience || "—"}</strong></div>
                <div><span>{sw ? "Tarehe ya usajili" : "Registration date"}</span><strong>{new Date(item.created_at).toLocaleString(sw ? "sw-TZ" : "en-GB")}</strong></div>
              </div>
            </section>

            <section className="verification-panel">
              <div className="verification-panel-heading"><div><h2>{sw ? "Matokeo ya uhakiki" : "Verification checks"}</h2><p>{sw ? "Kila matokeo ni ushahidi wa ukaguzi; si uamuzi wa mwisho wa ombi." : "Each result is a review finding, not a final application decision."}</p></div><strong>{item.checks.filter((check) => check.status === "passed").length}/4</strong></div>
              <div className="verification-check-list">
                {item.checks.map((check) => {
                  const meta = checkMeta[check.check_type];
                  const resultValue = draftResults[check.id] ?? check.result_code;
                  const notesValue = draftNotes[check.id] ?? check.review_notes ?? "";
                  const isPassed = check.status === "passed" && check.result_code === passResult[check.check_type];
                  return <article className="verification-check-card" key={check.id}>
                    <div className="verification-check-title"><div><h3>{meta ? (sw ? meta.sw : meta.en) : check.check_type}</h3><p>{sw ? "Mbinu" : "Method"}: {check.method || (sw ? "Haijawekwa" : "Not recorded")}</p></div><span className={"verification-status status-" + check.status}>{check.status.replaceAll("_", " ")}</span></div>
                    {canReview && !finalDecisionMade ? <>
                      <label className="verification-field"><span>{sw ? "Matokeo ya chanzo" : "Source finding"}</span><select value={resultValue} onChange={(event) => setDraftResults((current) => ({ ...current, [check.id]: event.target.value }))}><option value="">{sw ? "Chagua matokeo" : "Select a result"}</option>{(meta?.results ?? []).map((option) => <option key={option.value} value={option.value}>{sw ? option.sw : option.en}</option>)}</select></label>
                      <label className="verification-field"><span>{sw ? "Maelezo ya ukaguzi" : "Review notes"}</span><textarea value={notesValue} onChange={(event) => setDraftNotes((current) => ({ ...current, [check.id]: event.target.value }))} rows={3} placeholder={sw ? "Andika maelezo ya ushahidi uliokagua…" : "Record concise notes about the evidence reviewed…"} /></label>
                      <div className="verification-actions"><button type="button" disabled={!!busy || !resultValue} onClick={() => void saveCheck(check, resultValue, notesValue)}>{busy === "check-" + check.id ? (sw ? "Inahifadhi…" : "Saving…") : (sw ? "Hifadhi matokeo" : "Save finding")}</button></div>
                    </> : <div className="verification-readonly"><p>{check.result_code || (sw ? "Hakuna matokeo" : "No result recorded")}</p>{check.review_notes ? <small>{check.review_notes}</small> : null}</div>}
                    {check.check_type === "driving_licence" ? <div className="verification-licence-box"><strong>{sw ? "Madarasa ya leseni yaliyothibitishwa" : "Verified licence classes"}</strong><div className="verification-tags">{check.verified_licence_classes.filter((entry) => entry.is_current).map((entry) => <span key={entry.id}>{entry.licence_class}</span>)}</div>{canReview && !finalDecisionMade && isPassed ? <div className="verification-licence-entry"><input value={licenceInput} onChange={(event) => setLicenceInput(event.target.value)} placeholder={sw ? "Mfano: A, B, C1" : "Example: A, B, C1"} aria-label={sw ? "Madarasa ya leseni" : "Licence classes"} /><button type="button" disabled={!!busy} onClick={() => void saveLicenceClasses(check)}>{sw ? "Hifadhi madarasa" : "Save classes"}</button></div> : null}</div> : null}
                  </article>;
                })}
              </div>
            </section>

            <section className="verification-panel">
              <div className="verification-panel-heading"><div><h2>{sw ? "Uamuzi wa mwisho" : "Final decision"}</h2><p>{sw ? "Uamuzi wa mwisho ni tofauti na matokeo ya ukaguzi." : "The final decision is separate from individual check findings."}</p></div></div>
              {item.status === "approved" ? <div className="verification-success">{sw ? "Uhakiki umeidhinishwa." : "Verification approved."} {item.profile_status === "active" ? (sw ? "Upatikanaji wa umma umewashwa." : "Public availability is active.") : (sw ? "Inasubiri msimamizi kuwezesha upatikanaji wa umma." : "Waiting for an Admin to activate public availability.")}</div> :
                item.status === "rejected" ? <div className="verification-alert">{sw ? "Ombi hili limekataliwa." : "This verification has been rejected."} {item.decision_reason}</div> :
                <>
                  <p className="verification-requirements">{allPassed ? (sw ? "Ukaguzi wote umepita." : "All four checks have passed.") : (sw ? "Ukaguzi wote minne lazima upite kabla ya kuidhinisha." : "All four checks must pass before approval.")} {!hasCurrentLicenceClass ? (sw ? " Darasa la leseni lililothibitishwa linahitajika pia." : " A current verified licence class is also required.") : ""}</p>
                  {canReject ? <label className="verification-field"><span>{sw ? "Sababu ya kukataa (inahitajika)" : "Rejection reason (required)"}</span><textarea value={decisionReason} onChange={(event) => setDecisionReason(event.target.value)} rows={3} /></label> : null}
                  <div className="verification-actions verification-decision-actions">
                    {canApprove ? <button type="button" disabled={!!busy || !allPassed || !hasCurrentLicenceClass} onClick={() => void runAction(`verification/operations/${id}/approve/`, "approve", sw ? "Uhakiki umeidhinishwa." : "Verification approved.")}>{busy === "approve" ? (sw ? "Inachakata…" : "Processing…") : (sw ? "Idhinisha uhakiki" : "Approve verification")}</button> : null}
                    {canReject ? <button type="button" className="is-danger" disabled={!!busy || !decisionReason.trim()} onClick={() => void runAction(`verification/operations/${id}/reject/`, "reject", sw ? "Ombi limekataliwa." : "Verification rejected.", { reason: decisionReason })}>{busy === "reject" ? (sw ? "Inachakata…" : "Processing…") : (sw ? "Kataa ombi" : "Reject application")}</button> : null}
                  </div>
                </>}
              {item.status === "approved" && canActivate && item.profile_status !== "active" ? <div className="verification-activate-box"><p>{sw ? "Uhakiki umekamilika. Washa upatikanaji wa dereva baada ya ukaguzi wako wa mwisho." : "Verification is complete. Activate the driver’s public availability after your final administrative review."}</p><button type="button" disabled={!!busy} onClick={() => void runAction(`verification/operations/${id}/activate/`, "activate", sw ? "Upatikanaji wa dereva umewashwa." : "Driver availability activated.")}>{busy === "activate" ? (sw ? "Inachakata…" : "Processing…") : (sw ? "Washa upatikanaji" : "Activate availability")}</button></div> : null}
            </section>

            <section className="verification-panel"><div className="verification-panel-heading"><div><h2>{sw ? "Historia ya ukaguzi" : "Review history"}</h2><p>{sw ? "Rekodi ya hatua zilizochukuliwa." : "Recorded review and decision events."}</p></div></div>
              {sortedEvents.length ? <div className="verification-history">{sortedEvents.map((event) => <article key={event.id}><span className="verification-history-dot" /><div><strong>{event.event_type.replaceAll("_", " ")}</strong><p>{event.notes || (event.previous_status + " → " + event.new_status)}</p><small>{new Date(event.created_at).toLocaleString(sw ? "sw-TZ" : "en-GB")}</small></div></article>)}</div> : <p className="verification-muted">{sw ? "Hakuna hatua zilizorekodiwa bado." : "No review events have been recorded yet."}</p>}
            </section>
          </>
        }
      </div>
    </main>
  );
}
