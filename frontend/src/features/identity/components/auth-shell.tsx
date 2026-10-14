import type { ReactNode } from "react";
import Link from "next/link";

export function AuthShell({
  eyebrow,
  title,
  description,
  children,
  footer,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <main className="auth-page">
      <header className="auth-header">
        <Link className="brand" href="/" aria-label="DIVS home">
          <span className="brand-mark" aria-hidden="true">D</span>
          <span>DIVS</span>
        </Link>
        <Link className="auth-header-link" href="/">Explore DIVS</Link>
      </header>
      <section className="auth-layout">
        <div className="auth-intro">
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p>{description}</p>
          <div className="auth-trust-note">
            Your account identifies you. Driver and client registration are separate steps.
          </div>
        </div>
        <section className="auth-panel">
          {children}
          {footer ? <div className="auth-panel-footer">{footer}</div> : null}
        </section>
      </section>
      <footer className="auth-footer">
        <span>DIVS · Driver Identification &amp; Verification System</span>
        <span>Account and verification information is handled with care.</span>
      </footer>
    </main>
  );
}
