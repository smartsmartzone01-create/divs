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
      </header>

      <section className="auth-layout">
        <section className="auth-panel" aria-labelledby="auth-title">
          <div className="auth-heading">
            <p className="eyebrow">{eyebrow}</p>
            <h1 id="auth-title">{title}</h1>
            <p>{description}</p>
          </div>
          {children}
          {footer ? <div className="auth-panel-footer">{footer}</div> : null}
        </section>
      </section>

      <footer className="auth-footer">
        <span>Protected sign-in. Your account information is handled securely by DIVS.</span>
      </footer>
    </main>
  );
}
