"use client";

import Script from "next/script";
import { useEffect, useRef, useState } from "react";
import { identityRequest } from "@/features/identity/api";

type GoogleCredentialResponse = { credential?: string };
type GoogleButtonOptions = {
  theme?: "outline" | "filled_blue" | "filled_black";
  size?: "large" | "medium" | "small";
  text?: "signin_with" | "signup_with" | "continue_with" | "signin";
  shape?: "rectangular" | "pill" | "circle" | "square";
  width?: string;
};
type GoogleIdentityApi = {
  initialize: (options: {
    client_id: string;
    callback: (response: GoogleCredentialResponse) => void;
  }) => void;
  renderButton: (element: HTMLElement, options: GoogleButtonOptions) => void;
};
declare global {
  interface Window {
    google?: { accounts?: { id?: GoogleIdentityApi } };
  }
}

export function GoogleSignInButton() {
  const buttonRef = useRef<HTMLDivElement>(null);
  const [scriptReady, setScriptReady] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_OIDC_CLIENT_ID;

  useEffect(() => {
    const googleId = window.google?.accounts?.id;
    if (!scriptReady || !clientId || !googleId || !buttonRef.current) return;

    googleId.initialize({
      client_id: clientId,
      callback: async ({ credential }) => {
        if (!credential) {
          setError("Google did not return a sign-in credential.");
          return;
        }
        setBusy(true);
        setError("");
        try {
          await identityRequest<{ session_id?: string }>("providers/google/sign-in", {
            method: "POST",
            body: { credential },
          });
          window.location.assign("/account");
        } catch (caught) {
          setError(caught instanceof Error ? caught.message : "Google sign-in failed.");
        } finally {
          setBusy(false);
        }
      },
    });
    googleId.renderButton(buttonRef.current, {
      theme: "outline",
      size: "large",
      text: "continue_with",
      shape: "rectangular",
      width: "280",
    });
  }, [clientId, scriptReady]);

  if (!clientId) {
    return <p className="auth-helper">Google sign-in will be available when DIVS Google OAuth is configured.</p>;
  }

  return (
    <div className="google-sign-in">
      <div className="auth-divider"><span>or continue with</span></div>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onReady={() => setScriptReady(true)}
      />
      <div className={busy ? "google-button-wrap is-busy" : "google-button-wrap"} ref={buttonRef} />
      {busy ? <p className="auth-helper">Connecting to Google…</p> : null}
      {error ? <p className="auth-error" role="alert">{error}</p> : null}
    </div>
  );
}
