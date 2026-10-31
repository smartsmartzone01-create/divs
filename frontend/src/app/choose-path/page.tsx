"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AuthShell } from "@/features/identity/components/auth-shell";
import { getCurrentAccount, getDriverRegistration, getClientRegistration } from "@/features/identity/api";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";

type Purpose = "driver" | "client";

export default function ChoosePathPage() {
  const router = useRouter();
  const { language, t } = useDIVSPreferences();
  const sw = language === "sw";
  const [selected, setSelected] = useState<Purpose | null>(null);
  const [driverExists, setDriverExists] = useState(false);
  const [clientExists, setClientExists] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadProfiles() {
    setLoading(true);
    setError("");
    try {
      await getCurrentAccount();
      const [driver, client] = await Promise.all([
        getDriverRegistration(),
        getClientRegistration(),
      ]);
      setDriverExists(Boolean(driver));
      setClientExists(Boolean(client));
    } catch (caught) {
      if (caught instanceof Error && /Authentication request failed|401|403/i.test(caught.message)) {
        router.replace("/sign-in?next=%2Fchoose-path");
        return;
      }
      setError(t.chooseLoadError);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProfiles();
  }, []);

  async function continueWithPurpose() {
    if (!selected) return;
    setNotice("");
    if (selected === "driver") {
      router.push("/driver/onboarding");
      return;
    }
    if (clientExists) {
      router.push("/account");
      return;
    }
    setNotice(t.chooseClientComing);
  }

  return (
    <AuthShell
      eyebrow={t.chooseEyebrow}
      title={t.chooseTitle}
      description={t.chooseDescription}
      footer={<Link href="/">{t.chooseBack}</Link>}
    >
      <div className="account-purpose-page">
        {loading ? <p className="auth-helper">{sw ? "Inapakia akaunti yako…" : "Checking your account…"}</p> : null}
        {error ? (
          <div className="account-purpose-actions">
            <p className="auth-error" role="alert">{error}</p>
            <button className="auth-secondary-button" type="button" onClick={() => void loadProfiles()}>{t.chooseRetry}</button>
          </div>
        ) : null}
        {!loading && !error ? (
          <>
            <div className="account-purpose-options" role="group" aria-label={t.chooseTitle}>
              <button type="button" className="account-purpose-option" aria-pressed={selected === "driver"} onClick={() => { setSelected("driver"); setNotice(""); }}>
                <span className="account-purpose-option-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24"><path d="M5 17h14l-1.5-7h-11L5 17Z" /><path d="m8 10 1-4h6l1 4M7 17v2m10-2v2M7 14h.01M17 14h.01" /></svg>
                </span>
                <strong>{t.chooseDriverTitle}</strong>
                <p>{t.chooseDriverCopy}</p>
                {driverExists ? <span className="account-purpose-selected">{t.chooseDriverExisting}</span> : null}
                {selected === "driver" ? <span className="account-purpose-selected">✓ {sw ? "Umechagua" : "Selected"}</span> : null}
              </button>
              <button type="button" className="account-purpose-option" aria-pressed={selected === "client"} onClick={() => { setSelected("client"); setNotice(""); }}>
                <span className="account-purpose-option-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m15.5 15.5 5 5" /></svg>
                </span>
                <strong>{t.chooseClientTitle}</strong>
                <p>{t.chooseClientCopy}</p>
                {clientExists ? <span className="account-purpose-selected">{t.chooseClientExisting}</span> : null}
                {selected === "client" ? <span className="account-purpose-selected">✓ {sw ? "Umechagua" : "Selected"}</span> : null}
              </button>
            </div>
            {notice ? <p className="account-purpose-note" role="status">{notice}</p> : null}
            <div className="account-purpose-actions">
              <button className="auth-primary-button" type="button" disabled={!selected || busy} onClick={() => void continueWithPurpose()}>
                {t.chooseContinue}
              </button>
              <Link className="account-purpose-back" href="/">{t.chooseBack}</Link>
            </div>
          </>
        ) : null}
      </div>
    </AuthShell>
  );
}
