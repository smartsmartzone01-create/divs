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
  const isAdmin = access?.role === "admin";
  const roleLabel = isAdmin ? (sw ? "Msimamizi" : "Administrator") : (sw ? "Mwendeshaji" : "Operations operator");
  const accountLabel = account?.email || account?.phone_number || (sw ? "Akaunti ya DIVS" : "DIVS account");
  const initials = isAdmin ? "A" : "O";

  if (loading) {
    return <main className="workspace-shell admin-workspace"><WorkspaceHeader /><div className="admin-workspace-content"><p className="workspace-muted">{sw ? "Inapakia nafasi yako ya DIVS…" : "Loading your DIVS workspace…"}</p></div></main>;
  }

  if (error && !access) {
    return <main className="workspace-shell admin-workspace"><WorkspaceHeader /><div className="admin-workspace-content"><section className="admin-panel"><h1 className="admin-title">{sw ? "Nafasi ya kazi haipatikani" : "Workspace unavailable"}</h1><p className="admin-error" role="alert">{error}</p><Link className="admin-link" href="/sign-in">{sw ? "Rudi kuingia" : "Return to sign in"}</Link></section></div></main>;
  }

  return (
    <main className="workspace-shell admin-workspace">
      <WorkspaceHeader />
      <div className="admin-workspace-content">
        <section className="admin-profile-hero">
          <div className="admin-avatar" aria-hidden="true">{initials}</div>
          <p className="admin-eyebrow">{sw ? "Uendeshaji wa DIVS" : "DIVS OPERATIONS"}</p>
          <h1>{roleLabel}</h1>
          <span className="admin-status-pill">{sw ? "Ruhusa imethibitishwa" : "Access approved"}</span>
          <p className="admin-profile-meta">{accountLabel}</p>
          <p className="admin-profile-copy">{sw ? "Simamia shughuli za mfumo kulingana na ruhusa ulizopewa." : "Manage system operations within your approved permissions."}</p>
        </section>

        <section className="admin-stat-row" aria-label={sw ? "Viashiria vya uendeshaji" : "Operations indicators"}>
          <div><strong>{isAdmin ? (sw ? "Msimamizi" : "Admin") : (sw ? "Mwendeshaji" : "Operator")}</strong><span>{sw ? "Aina ya ruhusa" : "Access role"}</span></div>
          <div><strong>{unread}</strong><span>{sw ? "Arifa ambazo hazijasomwa" : "Unread notifications"}</span></div>
          <div><strong>{canReviewApplications ? applications.length : "—"}</strong><span>{sw ? "Maombi yanayosubiri" : "Pending applications"}</span></div>
        </section>

        {error ? <p className="admin-error" role="alert">{error}</p> : null}

        <section className="admin-feature-grid">
          <a href="#recent-activity" className="admin-feature-card">
            <span className="admin-feature-icon is-blue" aria-hidden="true">⌁</span>
            <span className="admin-feature-copy"><strong>{sw ? "Arifa za uendeshaji" : "Operations notifications"}</strong><span>{unread ? (sw ? `${unread} hazijasomwa` : `${unread} unread`) : (sw ? "Hakuna arifa mpya" : "No unread notifications")}</span></span>
            <span className="admin-feature-count">{unread}</span>
          </a>
          {canReviewApplications ? (
            <Link href="/workspace/admin/applications" className="admin-feature-card">
              <span className="admin-feature-icon is-amber" aria-hidden="true">✓</span>
              <span className="admin-feature-copy"><strong>{sw ? "Maombi ya uendeshaji" : "Operations applications"}</strong><span>{sw ? "Kagua waombaji wa Admin na Operator" : "Review Admin and Operator applicants"}</span></span>
              <span className="admin-feature-count is-amber">{applications.length}</span>
            </Link>
          ) : (
            <div className="admin-feature-card is-muted">
              <span className="admin-feature-icon" aria-hidden="true">✓</span>
              <span className="admin-feature-copy"><strong>{sw ? "Maombi ya uendeshaji" : "Operations applications"}</strong><span>{sw ? "Eneo hili linapatikana kwa wasimamizi wenye ruhusa." : "This area is available to authorized administrators."}</span></span>
            </div>
          )}
        </section>

        <section className="admin-link-section">
          <h2>{sw ? "Sehemu za kazi" : "Workspace sections"}</h2>
          <div className="admin-horizontal-links">
            <a href="#recent-activity"><span aria-hidden="true">◉</span>{sw ? "Arifa" : "Notifications"}<small>{unread || ""}</small></a>
            {canReviewApplications ? <Link href="/workspace/admin/applications"><span aria-hidden="true">✓</span>{sw ? "Maombi" : "Applications"}<small>{applications.length || ""}</small></Link> : null}
            <span className="is-coming"><span aria-hidden="true">⌕</span>{sw ? "Uhakiki" : "Verification"}</span>
            <span className="is-coming"><span aria-hidden="true">▤</span>{sw ? "Madereva" : "Drivers"}</span>
            <span className="is-coming"><span aria-hidden="true">↗</span>{sw ? "Utendaji" : "Performance"}</span>
          </div>
        </section>

        <section id="recent-activity" className="admin-panel">
          <div className="admin-section-heading">
            <div><h2>{sw ? "Yanayohitaji uangalizi wako" : "Needs your attention"}</h2><p>{sw ? "Arifa na kazi zinazohitaji kufuatiliwa." : "Notifications and work that may need follow-up."}</p></div>
            <strong className="admin-count">{unread}</strong>
          </div>

          {canReviewApplications && applications.length > 0 ? (
            <Link href="/workspace/admin/applications" className="admin-attention-card">
              <span className="admin-attention-icon" aria-hidden="true">!</span>
              <span><strong>{sw ? "Maombi ya kujiunga na uendeshaji" : "Operations access applications"}</strong><small>{sw ? "Kagua waombaji wa nafasi za Msimamizi au Mwendeshaji." : "Review applicants requesting an Admin or Operator role."}</small></span>
              <b>{applications.length}</b>
            </Link>
          ) : null}

          {notifications.length ? (
            <div className="admin-notice-list">
              {notifications.slice(0, 5).map((item) => (
                <article key={item.id} className={item.read_at ? "" : "is-unread"}>
                  <span className="admin-notice-dot" />
                  <div><strong>{item.title}</strong><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString(sw ? "sw-TZ" : "en-US")}</small></div>
                </article>
              ))}
            </div>
          ) : applications.length === 0 ? (
            <div className="admin-empty-state"><strong>{sw ? "Umemaliza kazi za sasa" : "You're all caught up"}</strong><p>{sw ? "Hakuna arifa mpya za uendeshaji." : "There are no new operations notifications."}</p></div>
          ) : null}
        </section>

        <section className="admin-panel">
          <div className="admin-section-heading"><div><h2>{sw ? "Zana za usimamizi" : "Management areas"}</h2><p>{sw ? "Sehemu zinazojengwa kwa ajili ya shughuli zako." : "Areas being prepared for your operational responsibilities."}</p></div></div>
          <div className="admin-management-list">
            {[
              { title: sw ? "Uhakiki wa madereva" : "Driver verification", description: sw ? "Kagua utambulisho, leseni na rekodi." : "Review identity, licence and record checks.", status: sw ? "Inakuja" : "Coming next" },
              { title: sw ? "Usimamizi wa madereva" : "Driver management", description: sw ? "Kagua taarifa na wasifu wa madereva." : "Review driver records and profiles.", status: sw ? "Inakuja" : "Coming next" },
              { title: sw ? "Utendaji na rufaa" : "Performance & appeals", description: sw ? "Kagua matukio ya utendaji na rufaa." : "Review performance events and appeals.", status: sw ? "Inakuja" : "Coming next" },
            ].map((item) => <div className="admin-management-row" key={item.title}><span><strong>{item.title}</strong><small>{item.description}</small></span><em>{item.status}</em></div>)}
            <Link href="/account" className="admin-management-row admin-management-account"><span><strong>{sw ? "Akaunti na vipindi" : "Account & sessions"}</strong><small>{sw ? "Simamia kuingia na vifaa vyako." : "Manage your sign-in and devices."}</small></span><b>{sw ? "Fungua" : "Open"}</b></Link>
          </div>
        </section>

        <footer className="admin-workspace-footer">DIVS · {sw ? "Nafasi ya uendeshaji" : "Operations workspace"}</footer>
      </div>
    </main>
  );
}
