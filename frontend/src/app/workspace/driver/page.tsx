"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { logout } from "@/features/identity/api";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";

type Registration = {
  first_name: string; middle_name: string; last_name: string; nationality: string;
  region: string; district: string; residential_area: string; driving_experience: string;
  contact_email: string | null; contact_phone_number: string | null;
};
type DriverProfile = { id: string; status: "active" | "suspended" | "closed"; registration: Registration; created_at: string };
type Check = { id: string; check_type: string; status: string; method: string; result_code: string; checked_at: string | null; verified_licence_classes: { id: string; licence_class: string; is_current: boolean; verified_at: string }[] };
type Verification = { id: string; status: string; checks: Check[]; is_discoverable: boolean; decided_at: string | null };
type Performance = { score: { effective_score: number | null; calculated_score: number | null; manual_override_score: number | null } | null; history: { id: string; change_type: string; previous_score: number | null; new_score: number | null; reason: string; created_at: string }[]; active_restrictions: { id: string; kind: string; status: string; reason: string }[]; score_status: string };
type Appeal = { id: string; status: string; reason: string; created_at: string };
type Notice = { id: string; title: string; message: string; created_at: string; read_at: string | null };
type ApiResult<T> = { data: T | null; error: string };

async function readApi<T>(url: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(url, { credentials: "same-origin", cache: "no-store", headers: { Accept: "application/json" } });
    if (!response.ok) return { data: null, error: response.status === 404 ? "not_found" : `Request failed (${response.status})` };
    return { data: await response.json() as T, error: "" };
  } catch {
    return { data: null, error: "network" };
  }
}

const checkLabels: Record<string, { en: string; sw: string }> = {
  national_identity: { en: "Identity verification", sw: "Uhakiki wa utambulisho" },
  driving_licence: { en: "Driving licence", sw: "Leseni ya udereva" },
  traffic_records: { en: "Traffic records", sw: "Rekodi za usalama barabarani" },
  accident_records: { en: "Accident records", sw: "Rekodi za ajali" },
};
const experienceLabels: Record<string, { en: string; sw: string }> = {
  none: { en: "No professional experience", sw: "Hakuna uzoefu wa kitaalamu" },
  under_1_year: { en: "Less than 1 year", sw: "Chini ya mwaka 1" },
  "1_to_3_years": { en: "1–3 years experience", sw: "Uzoefu wa miaka 1–3" },
  "4_to_7_years": { en: "4–7 years experience", sw: "Uzoefu wa miaka 4–7" },
  "8_plus_years": { en: "8+ years experience", sw: "Uzoefu wa miaka 8 au zaidi" },
};

function statusLabel(value: string, sw: boolean) {
  const labels: Record<string, [string, string]> = {
    pending: ["Pending", "Inasubiri"], in_review: ["In review", "Inakaguliwa"],
    approved: ["Approved", "Imeidhinishwa"], rejected: ["Rejected", "Imekataliwa"],
    passed: ["Passed", "Imepita"], failed: ["Failed", "Haijapita"],
    needs_review: ["Needs review", "Inahitaji ukaguzi"], unavailable: ["Unavailable", "Haipatikani"],
    active: ["Active", "Inatumika"], suspended: ["Suspended", "Imesimamishwa"],
    closed: ["Closed", "Imefungwa"], submitted: ["Submitted", "Imewasilishwa"],
    upheld: ["Upheld", "Imekubaliwa"], denied: ["Denied", "Imekataliwa"],
  };
  return labels[value]?.[sw ? 1 : 0] ?? value.replace(/_/g, " ");
}

function StatusPill({ value, sw }: { value: string; sw: boolean }) {
  const tone = ["approved", "passed", "active", "upheld"].includes(value) ? "success" : ["rejected", "failed", "suspended", "denied"].includes(value) ? "danger" : "pending";
  return <span className={`driver-status-pill is-${tone}`}>{statusLabel(value, sw)}</span>;
}

function Icon({ name }: { name: string }) {
  const paths: Record<string, string> = {
    shield: "M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z M9 12l2 2 4-4",
    chart: "M3 3v18h18 M18 17V9 M13 17V5 M8 17v-3",
    appeal: "M4 4h16v13H8l-4 4V4Z M8 9h8 M8 13h5",
    bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9 M10 21h4",
    requests: "M8 6h13 M8 12h13 M8 18h13 M3 6h.01 M3 12h.01 M3 18h.01",
    clock: "M12 8v4l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z",
    file: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z M14 2v6h6 M8 13h8 M8 17h8",
    chevron: "m9 18 6-6-6-6",
    settings: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.8 1.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5v.1h-2.6v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1-1.8-1.8.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H6.4v-2.6h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1 1.8-1.8.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5v-.1H15v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.8 1.8-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.5 1h.1V14h-.1a1.7 1.7 0 0 0-1.5 1Z",
  logout: "M10 17l5-5-5-5 M15 12H3 M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6",
  edit: "M12 20h9 M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z",
};
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d={paths[name] ?? paths.file}/></svg>;
}

export default function DriverWorkspacePage() {
  const router = useRouter();
  const { language, setLanguage, theme, toggleTheme } = useDIVSPreferences();
  const sw = language === "sw";
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [verification, setVerification] = useState<Verification | null>(null);
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [appeals, setAppeals] = useState<Appeal[]>([]);
  const [notifications, setNotifications] = useState<Notice[]>([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);
  const [error, setError] = useState("");
  const [dataWarnings, setDataWarnings] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    async function load() {
      const [p, v, s, a, n] = await Promise.all([
        readApi<DriverProfile>("/api/backend/profiles/driver/"),
        readApi<Verification>("/api/backend/verification/driver/me/"),
        readApi<Performance>("/api/backend/performance/driver/me/"),
        readApi<Appeal[]>("/api/backend/performance/driver/appeals/"),
        readApi<{ unread_count: number; results: Notice[] }>("/api/backend/notifications/driver/"),
      ]);
      if (!active) return;
      if (p.data) setProfile(p.data);
      else if (p.error === "not_found") router.replace("/driver/onboarding");
      else setError(sw ? "Imeshindikana kupakia wasifu wako." : "We couldn't load your driver profile.");
      if (v.data) setVerification(v.data);
      if (s.data) setPerformance(s.data);
      if (a.data) setAppeals(a.data);
      if (n.data) setNotifications(n.data.results ?? []);
      const warnings = [v, s, a, n].filter((item) => item.error && item.error !== "not_found").length;
      if (warnings) setDataWarnings([sw ? "Baadhi ya taarifa hazikuweza kupakiwa." : "Some workspace information could not be loaded."]);
      setLoading(false);
    }
    void load();
    return () => { active = false; };
  }, [router, sw]);

  const registration = profile?.registration;
  const fullName = registration ? [registration.first_name, registration.middle_name, registration.last_name].filter(Boolean).join(" ") : "";
  const initials = fullName.split(/\s+/).filter(Boolean).map((part) => part[0]).slice(0, 2).join("").toUpperCase() || "D";
  const score = performance?.score?.effective_score ?? null;
  const currentLicenceClasses = useMemo(() => verification?.checks.flatMap((check) => check.verified_licence_classes ?? []).filter((item) => item.is_current).map((item) => item.licence_class) ?? [], [verification]);
  const unread = notifications.filter((item) => !item.read_at).length;
  const pendingAppeals = appeals.filter((item) => ["submitted", "pending", "in_review"].includes(item.status)).length;
  const verificationStatus = verification?.status ?? "pending";
  const experience = experienceLabels[registration?.driving_experience ?? ""]?.[sw ? "sw" : "en"] ?? (sw ? "Uzoefu haujawekwa" : "Experience not set");

  async function signOut() {
    setLoggingOut(true);
    try { await logout(); window.location.assign("/"); }
    catch { setError(sw ? "Imeshindikana kutoka. Jaribu tena." : "Could not sign out. Please try again."); setLoggingOut(false); }
  }

  if (loading) return <main className="workspace-shell driver-workspace"><header className="driver-workspace-header"><Link href="/" className="driver-brand">DIVS</Link></header><div className="driver-workspace-content"><p className="workspace-muted">{sw ? "Inapakia nafasi yako ya kazi…" : "Loading your workspace…"}</p></div></main>;
  if (!profile) return <main className="workspace-shell driver-workspace"><header className="driver-workspace-header"><Link href="/" className="driver-brand">DIVS</Link></header><div className="driver-workspace-content"><section className="driver-panel"><h1>{sw ? "Wasifu haupatikani" : "Profile unavailable"}</h1><p>{error}</p><Link href="/sign-in">{sw ? "Ingia tena" : "Sign in again"}</Link></section></div></main>;

  const checkRows = ["national_identity", "driving_licence", "traffic_records", "accident_records"].map((type) => ({
    type,
    check: verification?.checks.find((item) => item.check_type === type),
  }));

  return (
    <main className="workspace-shell driver-workspace">
      <header className="driver-workspace-header">
        <Link href="/" className="driver-brand" aria-label="DIVS home"><span className="driver-brand-symbol">D</span>DIVS</Link>
        <div className="driver-header-actions">
          <button className="driver-menu-button" type="button" aria-label={sw ? "Fungua menyu" : "Open menu"} aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}><span/><span/><span/></button>
        </div>
        {menuOpen ? <div className="driver-settings-menu">
          <p className="driver-settings-heading">{sw ? "Mipangilio ya jumla" : "General settings"}</p>
          <button type="button" onClick={() => setLanguage(sw ? "en" : "sw")}><span>{sw ? "Lugha" : "Language"}</span><strong>{sw ? "Kiswahili" : "English"}</strong></button>
          <button type="button" onClick={toggleTheme}><span>{sw ? "Mandhari" : "Appearance"}</span><strong>{theme === "light" ? (sw ? "Mwanga" : "Light") : (sw ? "Giza" : "Dark")}</strong></button>
          <Link href="#recent-activity" onClick={() => setMenuOpen(false)}><span>{sw ? "Arifa" : "Notifications"}</span><strong>{unread || (sw ? "Hakuna" : "None")}</strong></Link>
          <Link href="/account" onClick={() => setMenuOpen(false)}><span>{sw ? "Akaunti na vipindi" : "Account & sessions"}</span><Icon name="settings"/></Link>
          <button type="button" className="driver-menu-logout" onClick={() => void signOut()} disabled={loggingOut}><span>{loggingOut ? (sw ? "Inatoka…" : "Signing out…") : (sw ? "Toka" : "Sign out")}</span><Icon name="logout"/></button>
        </div> : null}
      </header>

      <div className="driver-workspace-content">
        <section className="driver-profile-hero">
          <div className="driver-avatar" aria-label={sw ? "Picha ya wasifu haijawekwa" : "No profile photo uploaded"}>{initials}</div>
          <h1>{fullName}</h1>
          <StatusPill value={profile.status === "active" ? verificationStatus : profile.status} sw={sw}/>
          <p className="driver-profile-meta">{[registration?.residential_area, registration?.district, registration?.region].filter(Boolean).join(" · ")}</p>
          <p className="driver-profile-experience">{experience}</p>
          <Link href="/driver/onboarding" className="driver-edit-profile"><Icon name="edit"/>{sw ? "Hariri wasifu" : "Edit profile"}</Link>
        </section>

        <section className="driver-stat-row" aria-label={sw ? "Viashiria vya dereva" : "Driver indicators"}>
          <div><strong>{score === null ? "—" : score}</strong><span>{sw ? "Alama" : "Score"}</span></div>
          <div><strong>{currentLicenceClasses.length ? currentLicenceClasses.join(", ") : "—"}</strong><span>{sw ? "Madaraja ya leseni" : "Licence classes"}</span></div>
          <div><strong>{performance?.active_restrictions.length ?? "—"}</strong><span>{sw ? "Vizuizi vinavyotumika" : "Active restrictions"}</span></div>
        </section>

        {dataWarnings.length > 0 ? <p className="driver-data-warning" role="status">{dataWarnings[0]}</p> : null}
        {error ? <p className="driver-data-warning" role="alert">{error}</p> : null}

        <section className="driver-feature-grid">
          <Link href="#verification" className="driver-feature-card">
            <span className="driver-feature-icon"><Icon name="shield"/></span>
            <span className="driver-feature-copy"><strong>{sw ? "Uhakiki" : "Verification"}</strong><span>{sw ? "Hali ya utambulisho, leseni na rekodi" : "Identity, licence and record checks"}</span></span>
            <StatusPill value={verificationStatus} sw={sw}/>
          </Link>
          <Link href="#performance" className="driver-feature-card">
            <span className="driver-feature-icon"><Icon name="chart"/></span>
            <span className="driver-feature-copy"><strong>{sw ? "Utendaji" : "Performance"}</strong><span>{score === null ? (sw ? "Alama bado haijaanzishwa" : "Your score is not established yet") : (sw ? `Alama yako ni ${score}/100` : `Your current score is ${score}/100`)}</span></span>
            <Icon name="chevron"/>
          </Link>
        </section>

        <section className="driver-link-section">
          <h2>{sw ? "Nafasi yako ya kazi" : "Your workspace"}</h2>
          <div className="driver-horizontal-links">
            <a href="#verification"><Icon name="shield"/><span>{sw ? "Uhakiki" : "Verification"}</span></a>
            <a href="#performance"><Icon name="chart"/><span>{sw ? "Utendaji" : "Performance"}</span></a>
            <a href="#appeals"><Icon name="appeal"/><span>{sw ? "Rufaa" : "Appeals"}</span><small>{pendingAppeals || ""}</small></a>
            <a href="#recent-activity"><Icon name="bell"/><span>{sw ? "Arifa" : "Notifications"}</span><small>{unread || ""}</small></a>
            <span className="is-coming"><Icon name="requests"/><span>{sw ? "Maombi" : "Requests"}</span></span>
            <span className="is-coming"><Icon name="clock"/><span>{sw ? "Upatikanaji" : "Availability"}</span></span>
            <span className="is-coming"><Icon name="file"/><span>{sw ? "Nyaraka" : "Documents"}</span></span>
          </div>
        </section>

        <section id="verification" className="driver-panel">
          <div className="driver-section-heading"><div><h2>{sw ? "Maendeleo ya uhakiki" : "Verification progress"}</h2><p>{sw ? "Hali rasmi ya kila ukaguzi unaohitajika." : "The recorded status of each required check."}</p></div><StatusPill value={verificationStatus} sw={sw}/></div>
          <div className="driver-check-list">
            {checkRows.map(({ type, check }) => <div className="driver-check-row" key={type}><span className="driver-check-mark"><Icon name="shield"/></span><div className="driver-check-copy"><strong>{checkLabels[type][sw ? "sw" : "en"]}</strong><small>{check?.method ? (check.method === "government_api" ? "Government API" : "Manual review") : (sw ? "Bado haijaanza" : "Not started")}</small></div><StatusPill value={check?.status ?? "pending"} sw={sw}/></div>)}
          </div>
          <p className="driver-panel-footnote">{verification?.is_discoverable ? (sw ? "Wasifu wako unaruhusiwa kuonekana kwenye utafutaji." : "Your profile is eligible to appear in driver discovery.") : (sw ? "Wasifu wako hautaonekana kwa wateja hadi masharti yote ya uhakiki na idhini yatimizwe." : "Your profile will not appear in public discovery until all verification and approval requirements are met.")}</p>
        </section>

        <section id="performance" className="driver-panel">
          <div className="driver-section-heading"><div><h2>{sw ? "Utendaji wako" : "Your performance"}</h2><p>{sw ? "Alama na historia yake." : "Your score and its recorded history."}</p></div>{score !== null ? <strong className="driver-score-large">{score}<small>/100</small></strong> : null}</div>
          {performance?.score_status === "not_established" || !performance?.score ? <p className="driver-empty-state">{sw ? "Alama yako itaanzishwa baada ya kuwa na taarifa za utendaji zinazostahili." : "Your score will be established when qualifying performance data becomes available."}</p> : null}
          {performance?.active_restrictions.length ? <div className="driver-restrictions"><strong>{sw ? "Vizuizi vinavyotumika" : "Active restrictions"}</strong>{performance.active_restrictions.map((item) => <p key={item.id}>{item.reason}</p>)}</div> : null}
          {performance?.history.length ? <div className="driver-history-list">{performance.history.slice(0, 4).map((item) => <div key={item.id}><span>{item.reason || item.change_type.replace(/_/g, " ")}</span><strong>{item.new_score ?? "—"}</strong></div>)}</div> : <p className="driver-empty-state">{sw ? "Hakuna mabadiliko ya alama yaliyorekodiwa bado." : "No score changes have been recorded yet."}</p>}
        </section>

        <section id="appeals" className="driver-panel">
          <div className="driver-section-heading"><div><h2>{sw ? "Rufaa zako" : "Your appeals"}</h2><p>{sw ? "Fuatilia rufaa ulizowasilisha." : "Track appeals you have submitted."}</p></div><strong className="driver-count">{appeals.length}</strong></div>
          {appeals.length ? <div className="driver-history-list">{appeals.slice(0, 4).map((item) => <div key={item.id}><span>{item.reason}</span><StatusPill value={item.status} sw={sw}/></div>)}</div> : <p className="driver-empty-state">{sw ? "Hujawasilisha rufaa yoyote." : "You have not submitted any appeals yet."}</p>}
          <p className="driver-panel-footnote">{sw ? "Unaweza kuwasilisha rufaa kuhusu tukio la utendaji linalostahili. Maamuzi hufanywa na timu ya uendeshaji." : "You can appeal eligible performance events. Decisions are made by the operations team."}</p>
        </section>

        <section id="recent-activity" className="driver-panel">
          <div className="driver-section-heading"><div><h2>{sw ? "Shughuli za hivi karibuni" : "Recent activity"}</h2><p>{sw ? "Arifa na masasisho ya akaunti yako." : "Notifications and updates about your account."}</p></div><strong className="driver-count">{unread}</strong></div>
          {notifications.length ? <div className="driver-notice-list">{notifications.slice(0, 5).map((item) => <article key={item.id} className={item.read_at ? "" : "is-unread"}><span className="driver-notice-dot"/><div><strong>{item.title}</strong><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString(sw ? "sw-TZ" : "en-US")}</small></div></article>)}</div> : <p className="driver-empty-state">{sw ? "Hakuna arifa mpya." : "No notifications yet."}</p>}
        </section>

        <footer className="driver-workspace-footer">DIVS · {sw ? "Nafasi binafsi ya dereva" : "Your personal driver workspace"}</footer>
      </div>
    </main>
  );
}
