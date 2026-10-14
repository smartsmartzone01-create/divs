"use client";

import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { confirmVerification, requestVerification } from "@/features/identity/api";

export function VerifyForm({
  initialChannel,
  initialTarget,
}: {
  initialChannel: "email" | "phone";
  initialTarget: string;
}) {
  const router = useRouter();
  const [channel, setChannel] = useState<"email" | "phone">(initialChannel);
  const [target, setTarget] = useState(initialTarget);
  const [code, setCode] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function sendCode() {
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const result = channel === "email"
        ? await requestVerification({ channel, email: target.trim() })
        : await requestVerification({ channel, phone_number: target.trim() });
      setNotice(result.detail);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not request a code.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const result = channel === "email"
        ? await confirmVerification({ channel, email: target.trim(), code })
        : await confirmVerification({ channel, phone_number: target.trim(), code });
      if (result.verified) {
        setNotice("Contact verified. You can now sign in.");
        window.setTimeout(() => router.replace("/sign-in"), 900);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The code could not be confirmed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-form">
      <div className="auth-field">
        <label>Verification method</label>
        <div className="auth-choice-row">
          <button type="button" className={channel === "email" ? "auth-choice is-selected" : "auth-choice"} onClick={() => { setChannel("email"); setTarget(""); setCode(""); setNotice(""); }}>
            Email
          </button>
          <button type="button" className={channel === "phone" ? "auth-choice is-selected" : "auth-choice"} onClick={() => { setChannel("phone"); setTarget(""); setCode(""); setNotice(""); }}>
            Phone
          </button>
        </div>
      </div>
      <div className="auth-field">
        <label htmlFor="verify-target">{channel === "email" ? "Email address" : "Phone number"}</label>
        <input
          id="verify-target"
          type={channel === "email" ? "email" : "tel"}
          required
          value={target}
          onChange={(event) => setTarget(event.target.value)}
          placeholder={channel === "email" ? "you@example.com" : "+255712345678"}
        />
      </div>
      <button className="auth-secondary-button" type="button" onClick={sendCode} disabled={busy || !target.trim()}>
        {busy ? "Please wait…" : "Send verification code"}
      </button>
      <form className="auth-form auth-form-nested" onSubmit={handleSubmit}>
        <div className="auth-field">
          <label htmlFor="verification-code">6-digit code</label>
          <input
            id="verification-code"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6}"
            maxLength={6}
            required
            value={code}
            onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
            placeholder="000000"
          />
        </div>
        {error ? <p className="auth-error" role="alert">{error}</p> : null}
        {notice ? <p className="auth-success" role="status">{notice}</p> : null}
        <button className="auth-primary-button" type="submit" disabled={busy || code.length !== 6}>
          {busy ? "Checking…" : "Verify contact"}
        </button>
      </form>
    </div>
  );
}
