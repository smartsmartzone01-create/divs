"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { registerAccount } from "@/features/identity/api";

type ContactMethod = "email" | "phone";

export function RegisterForm() {
  const router = useRouter();
  const [method, setMethod] = useState<ContactMethod>("email");
  const [contact, setContact] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const input = method === "email"
        ? { email: contact.trim(), password }
        : { phone_number: contact.trim(), password };
      await registerAccount(input);
      router.push(`/verify?channel=${method}&target=${encodeURIComponent(contact.trim())}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Registration failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <div className="auth-field">
        <label>Register using</label>
        <div className="auth-choice-row">
          <button type="button" className={method === "email" ? "auth-choice is-selected" : "auth-choice"} onClick={() => { setMethod("email"); setContact(""); }}>
            Email
          </button>
          <button type="button" className={method === "phone" ? "auth-choice is-selected" : "auth-choice"} onClick={() => { setMethod("phone"); setContact(""); }}>
            Phone
          </button>
        </div>
      </div>
      <div className="auth-field">
        <label htmlFor="contact">{method === "email" ? "Email address" : "Phone number"}</label>
        <input
          id="contact"
          type={method === "email" ? "email" : "tel"}
          autoComplete={method === "email" ? "email" : "tel"}
          inputMode={method === "email" ? "email" : "tel"}
          required
          value={contact}
          onChange={(event) => setContact(event.target.value)}
          placeholder={method === "email" ? "you@example.com" : "+255712345678"}
        />
        {method === "phone" ? <p className="auth-helper">Include the country code so DIVS can send a verification code.</p> : null}
      </div>
      <div className="auth-field">
        <label htmlFor="new-password">Create password</label>
        <input
          id="new-password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Choose a strong password"
        />
      </div>
      {error ? <p className="auth-error" role="alert">{error}</p> : null}
      <button className="auth-primary-button" type="submit" disabled={busy}>
        {busy ? "Creating account…" : "Create account"}
      </button>
      <p className="auth-helper">This creates your shared DIVS identity. Choose driver or client registration after verification.</p>
      <p className="auth-inline-link">Already registered? <Link href="/sign-in">Sign in</Link></p>
    </form>
  );
}
