"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { WorkspaceHeader } from "@/components/workspace/workspace-header";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";
import { apiRequest, ApiError } from "@/lib/api/client";

type Driver = {
  id: string;
  status: string;
  verification_status: string;
  created_at: string;
  registration: {
    first_name: string;
    middle_name: string;
    last_name: string;
    region: string;
    district: string;
    residential_area: string;
    driving_experience: string;
    contact_email: string | null;
    contact_phone_number: string | null;
  };
};
type DirectoryResponse = {
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: Driver[];
};
type Access = { role: "admin" | "operator"; capabilities: string[] };

function explainError(error: unknown, sw: boolean) {
  if (error instanceof ApiError) {
    const payload = error.payload as { detail?: string } | undefined;
    if (payload?.detail) return payload.detail;
    if (error.status === 403) return sw ? "Huna ruhusa ya kuona orodha ya madereva." : "You do not have permission to view the driver directory.";
  }
  return error instanceof Error ? error.message : (sw ? "Hitilafu imetokea." : "Something went wrong.");
}

function profileStatusLabel(status: string, sw: boolean) {
  const labels: Record<string, [string, string]> = {
    pending_activation: ["Pending activation", "Inasubiri kuanzishwa"],
    active: ["Active", "Hai"],
    suspended: ["Suspended", "Imesimamishwa"],
    closed: ["Closed", "Imefungwa"],
  };
  return labels[status]?.[sw ? 1 : 0] ?? status.replaceAll("_", " ");
}

function verificationStatusLabel(status: string, sw: boolean) {
  const labels: Record<string, [string, string]> = {
    not_started: ["Not started", "Haijaanza"],
    pending: ["Pending", "Inasubiri"],
    in_review: ["In review", "Inakaguliwa"],
    approved: ["Approved", "Imeidhinishwa"],
    rejected: ["Rejected", "Imekataliwa"],
  };
  return labels[status]?.[sw ? 1 : 0] ?? status.replaceAll("_", " ");
}

export default function AdminDriversPage() {
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  const [items, setItems] = useState<Driver[]>([]);
  const [access, setAccess] = useState<Access | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [profileStatus, setProfileStatus] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const query = new URLSearchParams();
      if (search) query.set("search", search);
      if (profileStatus) query.set("profile_status", profileStatus);
      if (verificationStatus) query.set("verification_status", verificationStatus);
      query.set("page", String(page));
      const [directory, permissions] = await Promise.all([
        apiRequest<DirectoryResponse>(`profiles/operations/drivers/?${query.toString()}`),
        apiRequest<Access>("operations/me/"),
      ]);
      setItems(directory.results ?? []);
      setCount(directory.count ?? 0);
      setTotalPages(Math.max(1, directory.total_pages ?? 1));
      setAccess(permissions);
    } catch (caught) {
      setError(explainError(caught, sw));
    } finally {
      setLoading(false);
    }
  }, [search, profileStatus, verificationStatus, page, sw]);

  useEffect(() => { void load(); }, [load]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  }

  const canView = !!access?.capabilities.includes("manage_driver_registrations");

  return (
    <main className="workspace-shell admin-workspace verification-workspace">
      <WorkspaceHeader />
      <div className="verification-content">
        <Link href="/workspace/admin" className="verification-back">← {sw ? "Nafasi ya uendeshaji" : "Operations workspace"}</Link>
        <header className="verification-page-heading">
          <p className="admin-eyebrow">{sw ? "OPERESHENI ZA DIVS" : "DIVS OPERATIONS"}</p>
          <h1>{sw ? "Usimamizi wa madereva" : "Driver management"}</h1>
          <p>{sw ? "Tafuta na kagua madereva wote waliosajiliwa. Hali ya akaunti na hali ya uhakiki huonyeshwa kando." : "Find and review all registered drivers. Account status and verification status are shown separately."}</p>
        </header>

        {error ? <p className="verification-alert" role="alert">{error}</p> : null}

        <section className="verification-summary">
          <div><strong>{loading ? "—" : count}</strong><span>{sw ? "Madereva waliosajiliwa" : "Registered drivers"}</span></div>
          <div><strong>{access?.role === "admin" ? (sw ? "Msimamizi" : "Admin") : access?.role === "operator" ? (sw ? "Mwendeshaji" : "Operator") : "—"}</strong><span>{sw ? "Jukumu lako" : "Your role"}</span></div>
          <div><strong>{items.length}</strong><span>{sw ? "Kwenye ukurasa huu" : "On this page"}</span></div>
        </section>

        <form className="verification-toolbar" onSubmit={submitSearch}>
          <label className="verification-search">
            <span>{sw ? "Tafuta dereva" : "Search drivers"}</span>
            <input value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder={sw ? "Jina, simu, barua pepe, mkoa au wilaya" : "Name, phone, email, region or district"} />
          </label>
          <button type="submit" className="verification-open-link">{sw ? "Tafuta" : "Search"}</button>
          <label className="verification-filter">
            <span>{sw ? "Hali ya akaunti" : "Account status"}</span>
            <select value={profileStatus} onChange={(event) => { setPage(1); setProfileStatus(event.target.value); }}>
              <option value="">{sw ? "Hali zote" : "All statuses"}</option>
              <option value="pending_activation">{sw ? "Inasubiri kuanzishwa" : "Pending activation"}</option>
              <option value="active">{sw ? "Hai" : "Active"}</option>
              <option value="suspended">{sw ? "Imesimamishwa" : "Suspended"}</option>
              <option value="closed">{sw ? "Imefungwa" : "Closed"}</option>
            </select>
          </label>
          <label className="verification-filter">
            <span>{sw ? "Hali ya uhakiki" : "Verification status"}</span>
            <select value={verificationStatus} onChange={(event) => { setPage(1); setVerificationStatus(event.target.value); }}>
              <option value="">{sw ? "Hali zote" : "All statuses"}</option>
              <option value="not_started">{sw ? "Haijaanza" : "Not started"}</option>
              <option value="pending">{sw ? "Inasubiri" : "Pending"}</option>
              <option value="in_review">{sw ? "Inakaguliwa" : "In review"}</option>
              <option value="approved">{sw ? "Imeidhinishwa" : "Approved"}</option>
              <option value="rejected">{sw ? "Imekataliwa" : "Rejected"}</option>
            </select>
          </label>
        </form>

        {!loading && !canView && !error ? <div className="verification-empty">{sw ? "Huna ruhusa ya kufikia eneo hili." : "You do not have access to this area."}</div> :
          loading ? <div className="verification-empty">{sw ? "Inapakia orodha ya madereva…" : "Loading driver directory…"}</div> :
          items.length === 0 ? <div className="verification-empty"><strong>{sw ? "Hakuna madereva waliopatikana" : "No drivers found"}</strong><p>{sw ? "Jaribu kubadilisha maneno ya utafutaji au vichujio." : "Try changing your search terms or filters."}</p></div> :
          <div className="verification-queue">
            {items.map((item) => {
              const driver = item.registration;
              const name = [driver.first_name, driver.middle_name, driver.last_name].filter(Boolean).join(" ");
              const initials = name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
              return (
                <article className="verification-queue-card" key={item.id}>
                  <div className="verification-queue-main">
                    <div className="verification-person-mark">{initials || "D"}</div>
                    <div className="verification-person">
                      <h2>{name || (sw ? "Dereva" : "Driver")}</h2>
                      <p>{[driver.residential_area, driver.district, driver.region].filter(Boolean).join(", ")}</p>
                      <small>{driver.contact_phone_number || driver.contact_email || (sw ? "Hakuna mawasiliano" : "No contact details")}</small>
                    </div>
                  </div>
                  <div className="verification-card-meta">
                    <span>{sw ? "Akaunti" : "Account"} <strong>{profileStatusLabel(item.status, sw)}</strong></span>
                    <span>{sw ? "Uhakiki" : "Verification"} <strong>{verificationStatusLabel(item.verification_status, sw)}</strong></span>
                    <span>{sw ? "Uzoefu" : "Experience"} <strong>{driver.driving_experience || "—"}</strong></span>
                    <span>{sw ? "Alisajiliwa" : "Registered"} <strong>{new Date(item.created_at).toLocaleDateString(sw ? "sw-TZ" : "en-GB")}</strong></span>
                  </div>
                  <p className="workspace-muted text-xs">{sw ? "Kitambulisho cha wasifu" : "Profile reference"}: {item.id}</p>
                  <p className="workspace-muted text-xs">{sw ? "Taarifa za kina na vitendo vya usimamizi vitaongezwa kwenye ukurasa wa dereva." : "Detailed records and management actions will be added to the individual driver page."}</p>
                </article>
              );
            })}
          </div>
        }

        {!loading && totalPages > 1 ? (
          <div className="mt-5 flex items-center justify-between gap-3">
            <button type="button" className="verification-open-link" disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>{sw ? "Iliyotangulia" : "Previous"}</button>
            <span className="workspace-muted text-sm">{sw ? `Ukurasa ${page} kati ya ${totalPages}` : `Page ${page} of ${totalPages}`}</span>
            <button type="button" className="verification-open-link" disabled={page >= totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>{sw ? "Ifuatayo" : "Next"}</button>
          </div>
        ) : null}
      </div>
    </main>
  );
}
