"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Application = { id: string; full_name: string; email: string | null; phone_number: string | null; role_applied_for: string; submitted_at: string };

export default function OperationsApplicationsPage() {
  const [items, setItems] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    setError("");
    try {
      const response = await fetch("/api/backend/operations/applications/pending/", { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error(response.status === 403 ? "Only the initial system superuser can review these applications." : `Could not load applications (${response.status}).`);
      setItems(await response.json() as Application[]);
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  async function decide(item: Application, decision: "approve" | "reject") {
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
      setNotice(payload.detail || "Application reviewed.");
    } catch (caught) {
      setError((caught as Error).message);
    } finally {
      setBusyId("");
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8 text-slate-900">
      <div className="mx-auto max-w-4xl">
        <Link href="/workspace/admin" className="text-sm font-semibold text-blue-800 hover:underline">← Admin workspace</Link>
        <div className="mt-6"><p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-700">Operations access</p><h1 className="mt-2 text-3xl font-bold">Pending applications</h1><p className="mt-2 text-slate-600">Review requests to join DIVS operations.</p></div>
        {error && <p role="alert" className="mt-5 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</p>}
        {notice && <p role="status" className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{notice}</p>}
        {loading ? <p className="mt-8 text-slate-500">Loading applications…</p> : items.length === 0 && !error ? <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-8 text-center"><h2 className="font-semibold">No pending applications</h2><p className="mt-1 text-sm text-slate-500">There are no operations access requests waiting for review.</p></div> : (
          <div className="mt-6 space-y-3">
            {items.map((item) => <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="font-semibold">{item.full_name}</h2><p className="mt-1 text-sm text-slate-600">{item.email || item.phone_number || "No contact supplied"}</p><p className="mt-1 text-xs text-slate-500">Requested role: {item.role_applied_for} · Submitted {new Date(item.submitted_at).toLocaleString()}</p></div><span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">Pending</span></div>
              <div className="mt-4 flex flex-wrap gap-2"><button disabled={!!busyId} onClick={() => void decide(item, "approve")} className="rounded-lg bg-[#153b67] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{busyId === item.id ? "Processing…" : "Approve"}</button><button disabled={!!busyId} onClick={() => void decide(item, "reject")} className="rounded-lg border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-700 disabled:opacity-50">Reject</button></div>
            </article>)}
          </div>
        )}
      </div>
    </main>
  );
}
