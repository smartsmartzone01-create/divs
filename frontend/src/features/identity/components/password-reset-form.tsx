"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { confirmPasswordReset, requestPasswordReset } from "@/features/identity/api";

export function PasswordResetForm() {
  const [method, setMethod] = useState<"email" | "phone">("email");
  const [target, setTarget] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function sendCode() {
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const result = method === "email"
        ? await requestPasswordReset({ email: target.trim() })
        : await requestPasswordReset({ phone_number: target.trim() });
      setNotice(result.detail);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not request a reset code.");
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
      const result = method === "email"
        ? await confirmPasswordReset({ email: target.trim(), code, new_password: password })
        : await confirmPasswordReset({ phone_number: target.trim(), code, new_password: password });
      setNotice(result.detail);
      setCode("");
      setPassword("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Password reset failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-form">
      <div className="auth-field">
        <label>Reset using</label>
        <div className="auth-choice-row">
          <button type="button" className={method === "email" ? "auth-choice is-selected" : "auth-choice"} onClick={() => { setMethod("email"); setTarget(""); setCode(""); }}>
            Email
          </button>
          <button type="button" className={method === "phone" ? "auth-choice is-selected" : "auth-choice"} onClick={() => { setMethod("phone"); setTarget(""); setCode(""); }}>
            Phone
          </button>
        </div>
      </div>
      <div className="auth-field">
        <label htmlFor="reset-target">{method === "email" ? "Verified email address" : "Verified phone number"}</label>
        <input
          id="reset-target"
          type={method === "email" ? "email" : "tel"}
          required
          value={target}
          onChange={(event) => setTarget(event.target.value)}
          placeholder={method === "email" ? "you@example.com" : "+255712345678"}
        />
      </div>
      <button className="auth-secondary-button" type="button" onClick={sendCode} disabled={busy || !target.trim()}>
        {busy ? "Please wait…" : "Send reset code"}
      </button>
      <form className="auth-form auth-form-nested" onSubmit={handleSubmit}>
        <div className="auth-field">
          <label htmlFor="reset-code">6-digit reset code</label>
          <input id="reset-code" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))} placeholder="000000" />
        </div>
        <div className="auth-field">
          <label htmlFor="reset-password">New password</label>
          <input id="reset-password" type="password" autoComplete="new-password" minLength={8} required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Choose a strong password" />
        </div>
        {error ? <p className="auth-error" role="alert">{error}</p> : null}
        {notice ? <p className="auth-success" role="status">{notice}</p> : null}
        <button className="auth-primary-button" type="submit" disabled={busy || code.length !== 6 || !password}>
          {busy ? "Resetting…" : "Reset password"}
        </button>
      </form>
      <p className="auth-inline-link"><Link href="/sign-in">Return to sign in</Link></p>
    </div>
  );
}
