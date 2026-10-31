"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { logout, getAccountMenuDetails, type AccountMenuDetails } from "@/features/identity/api";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";

export function UserAccountMenu() {
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  const [details, setDetails] = useState<AccountMenuDetails | null>({ displayName: "My account", initials: "U", roleLabel: "DIVS account", workspaceHref: "/account", workspaceLabel: "My account" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getAccountMenuDetails().then((value) => { if (active) setDetails(value); }).catch(() => { if (active) setDetails(null); });
    return () => { active = false; };
  }, []);

  async function handleSignOut() {
    setBusy(true);
    setError("");
    try {
      await logout();
      window.location.assign("/");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : (sw ? "Imeshindikana kutoka. Tafadhali jaribu tena." : "Could not sign out. Please try again."));
      setBusy(false);
    }
  }

  if (!details) return null;

  return (
    <details className="divs-account-menu landing-account-menu">
      <summary className="divs-account-avatar" aria-label={sw ? "Fungua menyu ya akaunti" : "Open account menu"} title={details.displayName}>
        {details.initials}
      </summary>
      <div className="divs-account-dropdown">
        <div className="divs-account-identity">
          <strong>{details.displayName}</strong>
          <span>{sw ? (details.roleLabel === "Administrator" ? "Msimamizi" : details.roleLabel === "Operations operator" ? "Mwendeshaji" : details.roleLabel === "Driver" ? "Dereva" : details.roleLabel === "Client" ? "Mteja" : "Akaunti ya DIVS") : details.roleLabel}</span>
        </div>
        <Link href={details.workspaceHref} className="divs-account-menu-link">{sw ? (details.workspaceHref === "/workspace/admin" ? "Fungua nafasi ya msimamizi" : details.workspaceHref === "/workspace/driver" ? "Fungua nafasi ya dereva" : "Akaunti yangu") : details.workspaceLabel}</Link>
        <Link href="/account" className="divs-account-menu-link">{sw ? "Akaunti na vipindi" : "Account & sessions"}</Link>
        {error ? <p className="divs-account-menu-error" role="alert">{error}</p> : null}
        <button type="button" className="divs-account-signout" onClick={() => void handleSignOut()} disabled={busy}>
          {busy ? (sw ? "Inatoka…" : "Signing out…") : (sw ? "Toka" : "Sign out")}
        </button>
      </div>
    </details>
  );
}
