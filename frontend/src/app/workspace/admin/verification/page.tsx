"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { WorkspaceHeader } from "@/components/workspace/workspace-header";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";
import { apiRequest, ApiError } from "@/lib/api/client";

type Registration = {
  first_name: string; middle_name: string; last_name: string; nationality: string;
  region: string; district: string; residential_area: string;
  driving_experience: string; contact_email: string | null; contact_phone_number: string | null;
};
type Verification = { id: string; status: string; profile_status: string; checks: { id: string; status: string }[]; registration: Registration; created_at: string; };
type QueueResponse = { count: number; results: Verification[] };
type Access = { role: "admin" | "operator"; capabilities: string[] };

function errorMessage(error: unknown, sw: boolean) {
  if ( error instanceof ApiError) {
    const payload = error.payload as { detail?: string } | undefined;
    if (payload?.detail) return payload.detail;
    if (error.status === 403) return sw ? "Huna ruhusa ya kuona foleni hii." : "You do not have permission to access this queue.";
  }
  return error instanceof Error ? error.message : (sw ? "Hitilafu imetokea." : "Something went wrong.");
}

export default function DriverVerificationQueuePage() {
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  const [items, setItems] = useState<Verification[]>([]);
  const [access, setAccess] = useState<Access | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      apiRequest<Access>("operations/me/"),
      apiRequest<QueueResponse>("verification/operations/queue/"),
    ]).then(([permissions, queue]) => {
      if (!active) return;
      setAccess(permissions);
      setItems(queue.results ?? []);
    }).catch((caught) => {
      if (active) setError(errorMessage(caught, sw));
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [sw]);

  const visible = useMemo(() => items.filter((item) => {
    const driver = item.registration;
    const fullName = [driver.first_name, driver.middle_name, driver.last_name].filter(Boolean).join(" ");
    const term = search.trim().toLowerCase();
    const matchesSearch = !term || fullName.toLowerCase().includes(term)
      || driver.region.toLowerCase().includes(term) || driver.district.toLowerCase().includes(term);
    return matchesSearch && (filter === "all" || item.status === filter);
  }), [items, search, filter]);

  const passedCount = items.filter((item) => item.checks.length === 4 && item.checks.every((check) => check.status === "passed")).length;

  return (
    <main className="workspace-shell admin-workspace verification-workspace">
      <WorkspaceHeader />
      <div className="verification-content">
        <Link href="/workspace/admin" className="verification-back">← {sw ? "Nafasi ya uendeshaji" : "Operations workspace"}</Link>
        <header className="verification-page-heading">
          <p className="admin-eyebrow">{sw ? "OPERESHENI ZA DIVS" : "DIVS OPERATIONS"}</p>
          <h1>{sw ? "Uhakiki wa madereva" : "Driver verification"}</h1>
          <p>{sw ? "Kagua taarifa za usajili na matokeo ya uhakiki kabla ya uamuzi wa mwisho." : "Review driver registration details and verification findings before a final decision."}</p>
        </header>
        {error ? <p className="verification-alert" role="alert">{error}</p> : null}
        <section className="verification-summary">
          <div><strong>{items.length}</strong><span>{sw ? "Maombi yanayosubiri" : "Awaiting decision"}</span></div>
          <div><strong>{passedCount}</strong><span>{sw ? "Ukaguzi wote umepita" : "All checks passed"}</span></div>
          <div><strong>{access?.role === "admin" ? (sw ? "Msimamizi" : "Admin") : (sw ? "Mwendeshaji" : "Operator")}</strong><span>{sw ? "Jukumu lako" : "Your role"}</span></div>
        </section>
        <div className="verification-toolbar">
          <label className="verification-search"><span>{sw ? "Tafuta dereva" : "Search drivers"}</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={sw ? "Jina, mkoa au wilaya" : "Name, region or district"} /></label>
          <label className="verification-filter"><span>{sw ? "Hali" : "Status"}</span><select value={filter} onChange={(event) => setFilter(event.target.value)}><option value="all">{sw ? "Zote" : "All statuses"}</option><option value="pending">{sw ? "Inasubiri" : "Pending"}</option><option value="in_review">{sw ? "Inakaguliwa" : "In review"}</option></select></label>
        </div>
        {loading ? <div className="verification-empty">{sw ? "Inapakia maombi ya uhakiki…" : "Loading verification applications…"}</div> :
          visible.length === 0 ? <div className="verification-empty"><strong>{sw ? "Hakuna maombi yanayoonekana" : "No verification applications found"}</strong><p>{items.length === 0 ? (sw ? "Maombi mapya ya madereva yataonekana hapa." : "New driver applications will appear here.") : (sw ? "Jaribu kubadilisha utafutaji au kichujio." : "Try changing your search or status filter.")}</p></div> :
          <div className="verification-queue">{visible.map((item) => {
            const driver = item.registration;
            const name = [driver.first_name, driver.middle_name, driver.last_name].filter(Boolean).join(" ");
            const passed = item.checks.filter((check) => check.status === "passed").length;
            return <article className="verification-queue-card" key={item.id}>
              <div className="verification-queue-main">
                <div className="verification-person-mark">{name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase()}</div>
                <div className="verification-person"><h2>{name}</h2><p>{[driver.residential_area, driver.district, driver.region].filter(Boolean).join(", ")}</p><small>{driver.contact_phone_number || driver.contact_email || (sw ? "Hakuna mawasiliano" : "No contact details")}</small></div>
                <span className={"verification-status status-" + item.status}>{item.status.replaceAll("_", " ")}</span>
              </div>
              <div className="verification-card-meta"><span>{sw ? "Ukaguzi" : "Checks"} <strong>{passed}/4</strong></span><span>{sw ? "Uzoefu" : "Experience"} <strong>{driver.driving_experience || "—"}</strong></span><span>{sw ? "Imetumwa" : "Submitted"} <strong>{new Date(item.created_at).toLocaleDateString(sw ? "sw-TZ" : "en-GB")}</strong></span></div>
              <Link href={`/workspace/admin/verification/${item.id}`} className="verification-open-link">{sw ? "Fungua na kagua" : "Open application"} <span aria-hidden="true">→</span></Link>
            </article>;
          })}</div>
        }
      </div>
    </main>
  );
}
