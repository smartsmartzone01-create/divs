"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { GoogleSignInButton } from "@/features/identity/components/google-sign-in-button";
import type { AuthAccount, AuthSession } from "@/features/identity/api";
import { getCurrentAccount, getSessions, logout, revokeSession } from "@/features/identity/api";

export function AccountPanel() {
  const router = useRouter();
  const [account, setAccount] = useState<AuthAccount | null>(null);
  const [sessions, setSessions] = useState<AuthSession[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([getCurrentAccount(), getSessions()])
      .then(([current, activeSessions]) => {
        if (!active) return;
        setAccount(current);
        setSessions(activeSessions);
      })
      .catch(() => {
        if (active) router.replace("/sign-in");
      });
    return () => { active = false; };
  }, [router]);

  async function handleLogout() {
    setBusy(true);
    try {
      await logout();
    } finally {
      router.replace("/sign-in");
      router.refresh();
    }
  }

  async function handleRevoke(sessionId: string) {
    setError("");
    try {
      await revokeSession(sessionId);
      setSessions((current) => current.filter((session) => session.id !== sessionId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not revoke this session.");
    }
  }

  if (!account) {
    return <div className="auth-loading">Loading your account…</div>;
  }

  return (
    <div className="account-panel-content">
      <div className="account-summary">
        <span className="account-status-dot" aria-hidden="true" />
        <div>
          <p className="account-summary-label">Signed in</p>
          <h2>{account.email || account.phone_number}</h2>
          <p className="auth-helper">
            {account.email ? (account.email_verified ? "Email verified" : "Email not verified") : "No email added"}
            {account.phone_number ? ` · ${account.phone_verified ? "Phone verified" : "Phone not verified"}` : ""}
          </p>
        </div>
      </div>
      <GoogleSignInButton />
      <div className="account-actions">
        <Link className="auth-secondary-link" href="/verify">Verify a contact method</Link>
        <button className="auth-secondary-button" type="button" onClick={handleLogout} disabled={busy}>
          {busy ? "Signing out…" : "Sign out"}
        </button>
      </div>
      <section className="session-section">
        <div className="session-heading">
          <div>
            <h3>Signed-in devices</h3>
            <p>Revoke sessions you no longer recognize or use.</p>
          </div>
          <span className="session-count">{sessions.length}</span>
        </div>
        {error ? <p className="auth-error" role="alert">{error}</p> : null}
        {sessions.length ? sessions.map((session) => (
          <article className="session-card" key={session.id}>
            <div>
              <strong>{session.device_label || "Device / browser"}</strong>
              <p>Last active: {new Date(session.last_seen_at).toLocaleString()}</p>
              <p>Expires: {new Date(session.expires_at).toLocaleString()}</p>
              {session.current ? <span className="session-current">Current session</span> : null}
            </div>
            {session.current ? (
              <button className="session-revoke" type="button" onClick={handleLogout}>
                Sign out
              </button>
            ) : (
              <button className="session-revoke" type="button" onClick={() => handleRevoke(session.id)}>
                Revoke
              </button>
            )}
          </article>
        )) : <p className="auth-helper">No active sessions were returned.</p>}
      </section>
      <p className="auth-helper">This is your shared identity account. Driver and client registration are separate.</p>
    </div>
  );
}
