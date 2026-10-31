"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { logout, getAccountMenuDetails, type AccountMenuDetails } from "@/features/identity/api";

export function UserAccountMenu() {
  const [details, setDetails] = useState<AccountMenuDetails | null>(null);
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
      setError(caught instanceof Error ? caught.message : "Could not sign out. Please try again.");
      setBusy(false);
    }
  }

  if (!details) return null;

  return (
    <details className="divs-account-menu">
      <summary className="divs-account-avatar" aria-label="Open account menu" title={details.displayName}>
        {details.initials}
      </summary>
      <div className="divs-account-dropdown">
        <div className="divs-account-identity">
          <strong>{details.displayName}</strong>
          <span>{details.roleLabel}</span>
        </div>
        <Link href={details.workspaceHref} className="divs-account-menu-link">{details.workspaceLabel}</Link>
        <Link href="/account" className="divs-account-menu-link">Account &amp; sessions</Link>
        {error ? <p className="divs-account-menu-error" role="alert">{error}</p> : null}
        <button type="button" className="divs-account-signout" onClick={() => void handleSignOut()} disabled={busy}>
          {busy ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </details>
  );
}
