"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { WorkspaceHeader } from "@/components/workspace/workspace-header";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";

type Application = { id: string; full_name: string; email: string | null; phone_number: string | null; role_applied_for: string; submitted_at: string };

export default function OperationsApplicationsPage() {
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  const [items, setItems] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    setError("");
    try {
      const response = await fetch("/api/backend/operations/applications/pending/", { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error(response.status === 403 ? (sw ? "Msimamizi mkuu wa mfumo pekee ndiye anayeweza kukagua maombi haya." : "Only the initial system superuser can review these applications.") : `Could not load applications (${response.status}).`);
      setItems(await response.json() as Application[]);
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, [sw]);

  async function decide(item: Application, decision: "approved" | "rejected") {
    setBusyId(item.id); setError(""); setNotice("");
    try {
      const response = await fetch(`/api/backend/operations/applications/${item.id}/review/`, {
        method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ decision }),
      });
      const payload = await response.json().catch(() => ({})) as { detail?: string };
      if (!response.ok) throw new Error(payload.detail || `Review failed (${response.status}).`);
      setItems((current) => current.filter((entry) => entry.id !== item.id));
      setNotice(payload.detail || (sw ? "Ombi limekaguliwa." : "Application reviewed."));
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setBusyId("");
    }
  }

  return (
    <main className="workspace-shell">
      <WorkspaceHeader />
      <div className="workspace-content">
        <Link href="/workspace/admin" className="workspace-link text-sm">← {sw ? "Nafasi ya msimamizi" : "Admin workspace"}</Link>
        <div className="mt-6">
          <p className="workspace-eyebrow">{sw ? "Ruhusa za uendeshaji" : "Operations access"}</p>
          <h1 className="workspace-title">{sw ? "Maombi yanayosubiri" : "Pending applications"}</h1>
          <p className="workspace-description">{sw ? "Kagua maombi ya kujiunga na timu ya uendeshaji ya DIVS." : "Review requests to join DIVS operations."}</p>
        </div>
        {error && <p role="alert" className="workspace-alert mt-5">{error}</p>}
        {notice && <p role="status" className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{notice}</p>}
        {loading ? <p className="workspace-muted mt-8">{sw ? "Inapakia maombi…" : "Loading applications…"}</p> : items.length === 0 && !error ? (
          <div className="workspace-card mt-8 p-8 text-center"><h2 className="font-semibold">{sw ? "Hakuna maombi yanayosubiri" : "No pending applications"}</h2><p className="workspace-muted mt-1 text-sm">{sw ? "Hakuna maombi ya ruhusa za uendeshaji yanayosubiri ukaguzi." : "There are no operations access requests waiting for review."}</p></div>
        ) : (
          <div className="mt-6 grid gap-3">
            {items.map((item) => <article key={item.id} className="workspace-card">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0"><h2 className="font-semibold">{item.full_name}</h2><p className="workspace-muted mt-1 text-sm">{item.email || item.phone_number || (sw ? "Hakuna mawasiliano yaliyotolewa" : "No contact supplied")}</p><p className="workspace-muted mt-1 text-xs">{sw ? "Nafasi iliyoombwa" : "Requested role"}: {item.role_applied_for} · {sw ? "Imetumwa" : "Submitted"} {new Date(item.submitted_at).toLocaleString(sw ? "sw-TZ" : "en-US")}</p></div>
                <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-900">{sw ? "Inasubiri" : "Pending"}</span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button disabled={!!busyId} onClick={() => void decide(item, "approved")} className="rounded-lg bg-[#153b67] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{busyId === item.id ? (sw ? "Inachakata…" : "Processing…") : (sw ? "Idhinisha" : "Approve")}</button>
                <button disabled={!!busyId} onClick={() => void decide(item, "rejected")} className="rounded-lg border border-rose-300 px-4 py-2 text-sm font-semibold text-rose-700 disabled:opacity-50">{sw ? "Kataa" : "Reject"}</button>
              </div>
            </article>)}
          </div>
        )}
      </div>
    </main>
  );
}
