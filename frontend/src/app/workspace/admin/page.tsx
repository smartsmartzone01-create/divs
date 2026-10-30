"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Account = { id: string; email: string | null; phone_number: string | null };
type Access = { role: "admin" | "operator"; capabilities: string[] };
type Notification = { id: string; title: string; message: string; created_at: string; read_at: string | null };
type Application = { id: string; full_name: string; email: string | null; phone_number: string | null; role_applied_for: string; submitted_at: string };

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { credentials: "same-origin", cache: "no-store" });
  if (!response.ok) throw Object.assign(new Error(`Request failed (${response.status})`), { status: response.status });
  return response.json() as Promise<T>;
}

export default function AdminWorkspacePage() {
  const [account, setAccount] = useState<Account | null>(null);
  const [access, setAccess] = useState<Access | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);\n  const [canReviewApplications, setCanReviewApplications] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [accountResult, accessResult, notificationResult] = await Promise.all([
          getJson<Account>("/api/auth/me/"),
          getJson<Access>("/api/backend/operations/me/"),
          getJson<{ unread_count: number; results: Notification[] }>("/api/backend/notifications/operations/"),
        ]);
        if (!active) return;
        setAccount(accountResult);
        setAccess(accessResult);
        setNotifications(notificationResult.results ?? []);

        // Only the initial system superuser can review operations applications.
        // A 403 for an ordinary Admin is expected and is not shown as an error.
        if (accessResult.role === "admin") {
          try {
            const pending = await getJson<Application[]>("/api/backend/operations/applications/pending/");
            if (active) { setApplications(pending); setCanReviewApplications(true); }
          } catch (caught) {
            if ((caught as { status?: number }).status !== 403 && active) {
              setError("Could not load pending operations applications.");
            }
          }
        }
      } catch (caught) {
        if (active) setError((caught as Error).message || "Could not load your workspace.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, []);

  if (loading) {
    return <main className="min-h-screen bg-slate-50 px-5 py-12 text-slate-600"><div className="mx-auto max-w-5xl">Loading your DIVS workspace…</div></main>;
  }

  if (error && !access) {
    return <main className="min-h-screen bg-slate-50 px-5 py-12"><div className="mx-auto max-w-xl rounded-2xl border border-rose-200 bg-white p-6"><h1 className="text-xl font-semibold text-slate-900">Workspace unavailable</h1><p className="mt-2 text-sm text-rose-700">{error}</p><Link className="mt-4 inline-block font-semibold text-blue-800 underline" href="/sign-in">Return to sign in</Link></div></main>;
  }

  const roleLabel = access?.role === "admin" ? "Administrator" : "Operations operator";
  const unread = notifications.filter((item) => !item.read_at).length;

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-5">
          <Link href="/" className="text-xl font-extrabold tracking-[0.16em] text-[#153b67]">DIVS</Link>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden text-slate-500 sm:inline">{account?.email || account?.phone_number}</span>
            <Link href="/account" className="rounded-lg border border-slate-200 px-3 py-2 font-semibold hover:bg-slate-50">Account</Link>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-5 py-9">
        <div className="mb-8">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-700">Operations</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Admin workspace</h1>
          <p className="mt-2 max-w-2xl text-slate-600">Your access status, outstanding work and shortcuts to the areas you manage.</p>
        </div>

        <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm text-slate-500">Your operations status</p>
              <div className="mt-1 flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                <h2 className="text-xl font-semibold">Active</h2>
              </div>
              <p className="mt-1 text-sm text-slate-600">{roleLabel} · {account?.email || account?.phone_number}</p>
            </div>
            <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-sm font-semibold text-emerald-800">Access approved</span>
          </div>
        </section>

        <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <div><h2 className="text-lg font-semibold">Needs your attention</h2><p className="mt-1 text-sm text-slate-500">Items requiring follow-up in your workspace.</p></div>
              {unread > 0 && <span className="rounded-full bg-amber-50 px-3 py-1 text-sm font-semibold text-amber-800">{unread} unread</span>}
            </div>

            {applications.length > 0 && (
              <Link href="/workspace/admin/applications" className="mt-5 flex items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50/70 p-4 hover:border-amber-300">
                <div><p className="font-semibold">Operations access applications</p><p className="mt-1 text-sm text-slate-600">Review applicants requesting an Admin or Operator role.</p></div>
                <span className="rounded-full bg-white px-3 py-1 text-sm font-bold text-amber-900">{applications.length}</span>
              </Link>
            )}

            {notifications.length > 0 ? (
              <div className="mt-4 divide-y divide-slate-100">
                {notifications.slice(0, 5).map((item) => (
                  <article key={item.id} className="py-3">
                    <div className="flex items-start gap-2">
                      {!item.read_at && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-teal-600" />}
                      <div className="min-w-0"><h3 className="font-medium">{item.title}</h3><p className="mt-1 text-sm text-slate-600">{item.message}</p><p className="mt-1 text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</p></div>
                    </div>
                  </article>
                ))}
              </div>
            ) : applications.length === 0 ? (
              <div className="mt-5 rounded-xl bg-slate-50 px-4 py-8 text-center">
                <p className="font-semibold text-slate-800">You're all caught up</p>
                <p className="mt-1 text-sm text-slate-500">There are no new operations notifications.</p>
              </div>
            ) : null}
            {error && <p className="mt-3 text-sm text-rose-700">{error}</p>}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Workspace sections</h2>
            <p className="mt-1 text-sm text-slate-500">Go directly to a management area.</p>
            <div className="mt-4 space-y-2">
              {[
                { title: "Driver verification", description: "Review identity and licence checks", href: "/workspace/admin/verification", available: false },
                { title: "Driver management", description: "Review driver records and profiles", href: "/workspace/admin/drivers", available: false },
                { title: "Performance & appeals", description: "Review performance events and appeals", href: "/workspace/admin/performance", available: false },
                { title: "Operations access", description: "Review access applications", href: "/workspace/admin/applications", available: canReviewApplications },
              ].filter((item) => item.title !== "Operations access" || canReviewApplications).map((item) => (
                <div key={item.title} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 px-4 py-3">
                  <div><p className="font-semibold">{item.title}</p><p className="mt-0.5 text-xs text-slate-500">{item.description}</p></div>
                  {item.available ? <Link href={item.href} className="shrink-0 text-sm font-semibold text-blue-800 hover:underline">Open</Link> : <span className="shrink-0 text-xs text-slate-400">Coming next</span>}
                </div>
              ))}
              <Link href="/account" className="flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3 hover:bg-slate-50"><div><p className="font-semibold">Account & sessions</p><p className="mt-0.5 text-xs text-slate-500">Manage your sign-in and devices</p></div><span className="text-sm font-semibold text-blue-800">Open</span></Link>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
