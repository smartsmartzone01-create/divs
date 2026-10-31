"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { WorkspaceHeader } from "@/components/workspace/workspace-header";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";

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
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  const [account, setAccount] = useState<Account | null>(null);
  const [access, setAccess] = useState<Access | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [canReviewApplications, setCanReviewApplications] = useState(false);
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

        if (accessResult.role === "admin") {
          try {
            const pending = await getJson<Application[]>("/api/backend/operations/applications/pending/");
            if (active) { setApplications(pending); setCanReviewApplications(true); }
          } catch (caught) {
            if ((caught as { status?: number }).status !== 403 && active) {
              setError(sw ? "Imeshindikana kupakia maombi ya uanachama wa uendeshaji." : "Could not load pending operations applications.");
            }
          }
        }
      } catch (caught) {
        if (active) setError((caught as Error).message || (sw ? "Imeshindikana kufungua nafasi yako ya kazi." : "Could not load your workspace."));
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [sw]);

  const unread = notifications.filter((item) => !item.read_at).length;
  const roleLabel = access?.role === "admin" ? (sw ? "Msimamizi" : "Administrator") : (sw ? "Mwendeshaji" : "Operations operator");

  if (loading) {
    return <main className="workspace-shell"><WorkspaceHeader /><div className="workspace-content"><p className="workspace-muted">{sw ? "Inapakia nafasi yako ya DIVS…" : "Loading your DIVS workspace…"}</p></div></main>;
  }

  if (error && !access) {
    return <main className="workspace-shell"><WorkspaceHeader /><div className="workspace-content"><section className="workspace-card"><h1 className="workspace-title">{sw ? "Nafasi ya kazi haipatikani" : "Workspace unavailable"}</h1><p className="workspace-alert" role="alert">{error}</p><Link className="workspace-link" href="/sign-in">{sw ? "Rudi kuingia" : "Return to sign in"}</Link></section></div></main>;
  }

  return (
    <main className="workspace-shell">
      <WorkspaceHeader />
      <div className="workspace-content">
        <div className="mb-7">
          <p className="workspace-eyebrow">{sw ? "Uendeshaji" : "Operations"}</p>
          <h1 className="workspace-title">{sw ? "Nafasi ya msimamizi" : "Admin workspace"}</h1>
          <p className="workspace-description">{sw ? "Hali yako ya ruhusa, kazi zinazohitaji uangalizi na njia za mkato za maeneo unayosimamia." : "Your access status, outstanding work and shortcuts to the areas you manage."}</p>
        </div>

        <section className="workspace-card mb-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="workspace-muted text-sm">{sw ? "Hali yako ya uendeshaji" : "Your operations status"}</p>
              <div className="mt-1 flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /><h2 className="text-xl font-semibold">{sw ? "Inatumika" : "Active"}</h2></div>
              <p className="workspace-muted mt-1 text-sm">{roleLabel} · {account?.email || account?.phone_number}</p>
            </div>
            <span className="workspace-status">{sw ? "Ruhusa imethibitishwa" : "Access approved"}</span>
          </div>
        </section>

        <div className="workspace-grid">
          <section className="workspace-card">
            <div className="flex items-center justify-between gap-3">
              <div><h2 className="text-lg font-semibold">{sw ? "Yanayohitaji uangalizi wako" : "Needs your attention"}</h2><p className="workspace-muted mt-1 text-sm">{sw ? "Masuala yanayohitaji kufuatiliwa katika nafasi yako ya kazi." : "Items requiring follow-up in your workspace."}</p></div>
              {unread > 0 && <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-900">{unread} {sw ? "hayajasomwa" : "unread"}</span>}
            </div>

            {applications.length > 0 && (
              <Link href="/workspace/admin/applications" className="mt-5 flex items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50/70 p-4 text-slate-900 hover:border-amber-300">
                <div><p className="font-semibold">{sw ? "Maombi ya kujiunga na uendeshaji" : "Operations access applications"}</p><p className="mt-1 text-sm text-slate-600">{sw ? "Kagua waombaji wa nafasi za Msimamizi au Mwendeshaji." : "Review applicants requesting an Admin or Operator role."}</p></div>
                <span className="rounded-full bg-white px-3 py-1 text-sm font-bold text-amber-900">{applications.length}</span>
              </Link>
            )}

            {notifications.length > 0 ? (
              <div className="mt-4 divide-y" style={{ borderColor: "var(--workspace-border)" }}>
                {notifications.slice(0, 5).map((item) => (
                  <article key={item.id} className="py-3">
                    <div className="flex items-start gap-2">
                      {!item.read_at && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-teal-600" />}
                      <div className="min-w-0"><h3 className="font-medium">{item.title}</h3><p className="workspace-muted mt-1 text-sm">{item.message}</p><p className="workspace-muted mt-1 text-xs">{new Date(item.created_at).toLocaleString(language === "sw" ? "sw-TZ" : "en-US")}</p></div>
                    </div>
                  </article>
                ))}
              </div>
            ) : applications.length === 0 ? (
              <div className="workspace-card-muted mt-5 rounded-xl px-4 py-8 text-center">
                <p className="font-semibold">{sw ? "Umemaliza kazi za sasa" : "You're all caught up"}</p>
                <p className="workspace-muted mt-1 text-sm">{sw ? "Hakuna arifa mpya za uendeshaji." : "There are no new operations notifications."}</p>
              </div>
            ) : null}
            {error && <p className="mt-3 text-sm text-rose-700">{error}</p>}
          </section>

          <section className="workspace-card">
            <h2 className="text-lg font-semibold">{sw ? "Sehemu za nafasi ya kazi" : "Workspace sections"}</h2>
            <p className="workspace-muted mt-1 text-sm">{sw ? "Nenda moja kwa moja kwenye eneo la usimamizi." : "Go directly to a management area."}</p>
            <div className="workspace-list">
              {[
                { title: sw ? "Uhakiki wa madereva" : "Driver verification", description: sw ? "Kagua utambulisho na leseni" : "Review identity and licence checks", href: "/workspace/admin/verification", available: false },
                { title: sw ? "Usimamizi wa madereva" : "Driver management", description: sw ? "Kagua taarifa na wasifu wa madereva" : "Review driver records and profiles", href: "/workspace/admin/drivers", available: false },
                { title: sw ? "Utendaji na rufaa" : "Performance & appeals", description: sw ? "Kagua matukio ya utendaji na rufaa" : "Review performance events and appeals", href: "/workspace/admin/performance", available: false },
                { title: sw ? "Maombi ya uendeshaji" : "Operations access", description: sw ? "Kagua maombi ya ruhusa" : "Review access applications", href: "/workspace/admin/applications", available: canReviewApplications },
              ].filter((item) => item.title !== (sw ? "Maombi ya uendeshaji" : "Operations access") || canReviewApplications).map((item) => (
                <div key={item.title} className="workspace-list-item">
                  <div className="min-w-0"><p className="font-semibold">{item.title}</p><p className="workspace-muted mt-0.5 text-xs">{item.description}</p></div>
                  {item.available ? <Link href={item.href} className="workspace-link shrink-0 text-sm">{sw ? "Fungua" : "Open"}</Link> : <span className="workspace-muted shrink-0 text-xs">{sw ? "Inakuja" : "Coming next"}</span>}
                </div>
              ))}
              <Link href="/account" className="workspace-list-item workspace-link"><span><strong>{sw ? "Akaunti na vipindi" : "Account & sessions"}</strong><span className="workspace-muted mt-0.5 block text-xs font-normal">{sw ? "Simamia kuingia na vifaa vyako" : "Manage your sign-in and devices"}</span></span><span className="shrink-0 text-sm">{sw ? "Fungua" : "Open"}</span></Link>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
