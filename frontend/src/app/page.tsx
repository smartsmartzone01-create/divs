"use client";

import Link from "next/link";
import { useState } from "react";

const benefits = [
  {
    number: "01",
    title: "Verified qualifications",
    description:
      "See clear verification statuses and licence information validated through the available review process.",
  },
  {
    number: "02",
    title: "Performance insights",
    description:
      "Understand a driver's performance history and the reasons behind changes to their score.",
  },
  {
    number: "03",
    title: "A more responsible process",
    description:
      "Designed for authorized verification integrations, with manual review where required.",
  },
];

export default function HomePage() {
  const [menuOpen, setMenuOpen] = useState(false);

  function closeMenu() {
    setMenuOpen(false);
  }

  return (
    <main className="landing-page">
      <header className="landing-header">
        <Link className="landing-brand" href="/" aria-label="DIVS home" onClick={closeMenu}>
          <span className="landing-brand-mark" aria-hidden="true">
            D
          </span>
          <span className="landing-brand-copy">
            <strong>DIVS</strong>
            <small>Driver verification</small>
          </span>
        </Link>

        <button
          className="mobile-menu-toggle"
          type="button"
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={menuOpen}
          aria-controls="landing-navigation"
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>

        <nav
          className={`landing-navigation${menuOpen ? " is-open" : ""}`}
          id="landing-navigation"
          aria-label="Main navigation"
        >
          <a href="#how-it-works" onClick={closeMenu}>How it works</a>
          <a href="#verification" onClick={closeMenu}>Verification</a>
          <a href="#get-started" onClick={closeMenu}>Get started</a>
          <div className="landing-nav-actions">
            <Link className="landing-login-link" href="/sign-in" onClick={closeMenu}>Log in</Link>
            <Link className="landing-nav-cta" href="/register" onClick={closeMenu}>Create account</Link>
          </div>
        </nav>
      </header>

      <section className="landing-hero" aria-labelledby="landing-hero-title">
        <div className="landing-hero-content">
          <p className="landing-eyebrow">
            <span className="landing-eyebrow-dot" />
            A clearer way to choose a driver
          </p>
          <h1 id="landing-hero-title">
            Find the right driver.
            <span>Hire with confidence.</span>
          </h1>
          <p className="landing-hero-copy">
            Discover professional drivers, review their verified qualifications,
            and make more informed hiring decisions — all in one place.
          </p>
          <div className="landing-hero-actions">
            <a className="landing-button landing-button-primary" href="#get-started">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <circle cx="10.8" cy="10.8" r="6.8" />
                <path d="m16 16 4.2 4.2" />
              </svg>
              Search for a driver
            </a>
            <a className="landing-button landing-button-secondary" href="#how-it-works">
              Explore DIVS <span aria-hidden="true">↗</span>
            </a>
          </div>
          <div className="landing-hero-note">
            <span className="landing-note-icon" aria-hidden="true">✓</span>
            <p>Verification status is shown transparently, based on available evidence.</p>
          </div>
        </div>

        <div className="landing-hero-visual" aria-label="Illustration of driver verification information">
          <div className="visual-orbit visual-orbit-one" />
          <div className="visual-orbit visual-orbit-two" />
          <div className="visual-glow" />
          <div className="visual-card visual-card-main">
            <div className="visual-card-top">
              <span className="visual-card-label">DIVS VERIFICATION</span>
              <span className="visual-shield" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M12 3 19 6v5.2c0 4.6-3 7.8-7 9.8-4-2-7-5.2-7-9.8V6l7-3Z" />
                  <path d="m8.7 11.7 2.2 2.2 4.5-4.6" />
                </svg>
              </span>
            </div>
            <div className="visual-profile-row">
              <div className="visual-avatar" aria-hidden="true">
                <svg viewBox="0 0 64 64">
                  <circle cx="32" cy="22" r="12" />
                  <path d="M10 58c1.5-13 9.5-20 22-20s20.5 7 22 20" />
                </svg>
              </div>
              <div>
                <strong>Driver profile</strong>
                <span>Qualifications &amp; records</span>
              </div>
            </div>
            <div className="visual-divider" />
            <div className="visual-status-row">
              <span className="visual-status-icon" aria-hidden="true">✓</span>
              <div><strong>Identity review</strong><span>Status available when reviewed</span></div>
              <span className="visual-status-label">Status</span>
            </div>
            <div className="visual-status-row">
              <span className="visual-status-icon visual-status-icon-blue" aria-hidden="true">↗</span>
              <div><strong>Licence information</strong><span>Validated details</span></div>
              <span className="visual-status-label">Status</span>
            </div>
            <div className="visual-score-panel">
              <div><span>Performance insights</span><strong>Clear. Fair. Traceable.</strong></div>
              <div className="visual-score-bars" aria-hidden="true"><i /><i /><i /><i /><i /></div>
            </div>
            <p className="visual-disclaimer">Illustrative preview · not a live verification record</p>
          </div>
          <div className="visual-floating-badge">
            <span aria-hidden="true">✦</span>
            Built around trust
          </div>
        </div>
        <div className="landing-hero-bottom" aria-hidden="true">
          <span>IDENTIFY</span><i /><span>VERIFY</span><i /><span>DISCOVER</span>
        </div>
      </section>

      <section className="landing-trust-section" id="how-it-works" aria-labelledby="trust-title">
        <div className="landing-section-heading">
          <p className="landing-eyebrow">Confidence through clarity</p>
          <h2 id="trust-title">More than a name on a list.</h2>
          <p>Useful information to help people and businesses make better-informed driver hiring decisions.</p>
        </div>
        <div className="landing-benefit-grid" id="verification">
          {benefits.map((benefit) => (
            <article className="landing-benefit-card" key={benefit.number}>
              <span className="landing-benefit-number">{benefit.number}</span>
              <div className="landing-benefit-icon" aria-hidden="true">
                {benefit.number === "01" ? (
                  <svg viewBox="0 0 24 24"><path d="M12 3 19 6v5.2c0 4.6-3 7.8-7 9.8-4-2-7-5.2-7-9.8V6l7-3Z" /><path d="m8.7 11.7 2.2 2.2 4.5-4.6" /></svg>
                ) : benefit.number === "02" ? (
                  <svg viewBox="0 0 24 24"><path d="M4 19V5M4 19h17" /><path d="m7 15 4-4 3 2 6-7" /></svg>
                ) : (
                  <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="m8 12 2.5 2.5L16.5 8" /></svg>
                )}
              </div>
              <h3>{benefit.title}</h3>
              <p>{benefit.description}</p>
            </article>
          ))}
        </div>
        <p className="landing-integration-note">
          <span aria-hidden="true">i</span>
          Government verification integrations will be described as connected only when authorized services are live. Manual review may be used where available.
        </p>
      </section>

      <section className="landing-start-section" id="get-started" aria-labelledby="start-title">
        <div className="landing-start-intro">
          <p className="landing-eyebrow">Your next step</p>
          <h2 id="start-title">What brings you to DIVS?</h2>
          <p>Choose how you want to get started. You can explore public information before creating an account.</p>
        </div>
        <div className="landing-audience-grid">
          <article className="landing-audience-card">
            <div className="landing-audience-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M5 17h14l-1.5-7h-11L5 17Z" /><path d="m8 10 1-4h6l1 4M7 17v2m10-2v2M7 14h.01M17 14h.01" /></svg>
            </div>
            <p className="landing-audience-label">FOR DRIVERS</p>
            <h3>Build your professional profile.</h3>
            <p>Register, complete your profile, and follow your verification progress.</p>
            <Link className="landing-text-link" href="/register">Join as a driver <span aria-hidden="true">→</span></Link>
          </article>
          <article className="landing-audience-card landing-audience-card-featured">
            <div className="landing-audience-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M3 20h18M5 20V8l7-4 7 4v12M9 20v-5h6v5M9 10h.01M15 10h.01" /></svg>
            </div>
            <p className="landing-audience-label">FOR CLIENTS &amp; BUSINESSES</p>
            <h3>Find a driver for your needs.</h3>
            <p>Explore drivers and use verified information to support your hiring decision.</p>
            <Link className="landing-text-link" href="/sign-in">Find a driver <span aria-hidden="true">→</span></Link>
          </article>
        </div>
        <p className="landing-existing-account">Already have an account? <Link href="/sign-in">Log in here</Link></p>
      </section>

      <footer className="landing-footer">
        <Link className="landing-footer-brand" href="/">
          <span className="landing-brand-mark" aria-hidden="true">D</span>
          <span>DIVS</span>
        </Link>
        <p>Driver Identification &amp; Verification System</p>
        <a href="#landing-hero-title">Back to top ↑</a>
        <small>© {new Date().getFullYear()} DIVS. Built for more informed decisions.</small>
      </footer>
    </main>
  );
}
