"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { getPostLoginPath, signIn } from "@/features/identity/api";
import { GoogleSignInButton } from "@/features/identity/components/google-sign-in-button";

export function SignInForm() {
  const router = useRouter();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await signIn(identifier.trim(), password);
      const requestedNext = new URLSearchParams(window.location.search).get("next");
      const safeNext = requestedNext?.startsWith("/") && !requestedNext.startsWith("//") ? requestedNext : null;
      router.replace(safeNext || await getPostLoginPath());
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Sign-in failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
    <form className="auth-form" onSubmit={handleSubmit}>
      <div className="auth-field">
        <label htmlFor="identifier">Email or verified phone number</label>
        <input
          id="identifier"
          autoComplete="username"
          inputMode="text"
          required
          value={identifier}
          onChange={(event) => setIdentifier(event.target.value)}
          placeholder="you@example.com or +255..."
        />
      </div>
      <div className="auth-field">
        <div className="auth-label-row">
          <label htmlFor="password">Password</label>
          <Link href="/forgot-password">Forgot password?</Link>
        </div>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Enter your password"
        />
      </div>
      {error ? <p className="auth-error" role="alert">{error}</p> : null}
      <button className="auth-primary-button" type="submit" disabled={busy}>
        {busy ? "Signing in…" : "Sign in"}
      </button>
      <p className="auth-helper">Your email or phone must be verified before password sign-in.</p>
    </form>
    <GoogleSignInButton />
    </>
  );
}
