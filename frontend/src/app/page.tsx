"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getCurrentAccount, getPostLoginPath, type AuthAccount } from "@/features/identity/api";
import { UserAccountMenu } from "@/features/identity/components/user-account-menu";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";



export default function HomePage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [signedInAccount, setSignedInAccount] = useState<AuthAccount | null>(null);
  const { language, setLanguage, theme, toggleTheme, t } = useDIVSPreferences();

  useEffect(() => {
    let active = true;
    getCurrentAccount()
      .then((account) => { if (active) setSignedInAccount(account); })
      .catch(() => { if (active) setSignedInAccount(null); });
    return () => { active = false; };
  }, []);
  const benefits = [
    { number: "01", title: t.benefitOneTitle, description: t.benefitOneCopy },
    { number: "02", title: t.benefitTwoTitle, description: t.benefitTwoCopy },
    { number: "03", title: t.benefitThreeTitle, description: t.benefitThreeCopy },
  ];

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
            <small>{language === "en" ? "Driver verification" : "Uhakiki wa madereva"}</small>
          </span>
        </Link>

        <div className="landing-header-tools">
          {signedInAccount ? (
            <UserAccountMenu />
          ) : null}

          <button
            className={`mobile-menu-toggle${menuOpen ? " is-open" : ""}`}
            type="button"
            aria-label={menuOpen ? t.closeMenu : t.openMenu}
            aria-expanded={menuOpen}
            aria-controls="landing-navigation"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>

        <nav
          className={`landing-navigation${menuOpen ? " is-open" : ""}`}
          id="landing-navigation"
          aria-label="Main navigation"
        >
          <a href="#how-it-works" onClick={closeMenu}>{t.navHow}</a>
          <a href="#verification" onClick={closeMenu}>{t.navVerification}</a>
          <a href="#get-started" onClick={closeMenu}>{t.navGetStarted}</a>
          <div className="landing-preference-controls" aria-label={t.languageLabel}>
            <button className="landing-language-toggle" type="button" onClick={() => setLanguage(language === "en" ? "sw" : "en")} aria-label={t.languageLabel} title={t.languageLabel}>
              {language === "en" ? "SW" : "EN"}
            </button>
            <button className="landing-theme-toggle" type="button" onClick={toggleTheme} aria-label={theme === "light" ? t.themeToDark : t.themeToLight} title={theme === "light" ? t.themeToDark : t.themeToLight}>
              {theme === "light" ? (
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 15.5A8.5 8.5 0 0 1 8.5 3.5 8.5 8.5 0 1 0 20.5 15.5Z" /></svg>
              ) : (
                <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" /></svg>
              )}
            </button>
          </div>
          <div className="landing-nav-actions">
            {signedInAccount ? (
              <button className="landing-login-link landing-account-nav-button" type="button" onClick={async () => { closeMenu(); window.location.assign(await getPostLoginPath()); }}>{language === "sw" ? "Akaunti yangu" : "My account"}</button>
            ) : (
              <Link className="landing-login-link" href="/sign-in" onClick={closeMenu}>{t.login}</Link>
            )}
            {!signedInAccount ? <Link className="landing-nav-cta" href="/register" onClick={closeMenu}>{t.createAccount}</Link> : null}
          </div>
        </nav>
      </header>

      <section className="landing-hero" aria-labelledby="landing-hero-title">
        <div className="landing-hero-content">
          <p className="landing-eyebrow">
            <span className="landing-eyebrow-dot" />
            {t.eyebrow}
          </p>
          <h1 id="landing-hero-title">
            {t.heroLineOne}
            <span>{t.heroLineTwo}</span>
          </h1>
          <p className="landing-hero-copy">
            {t.heroCopy}
          </p>
          <div className="landing-hero-actions">
            <a className="landing-button landing-button-primary" href="#get-started">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <circle cx="10.8" cy="10.8" r="6.8" />
                <path d="m16 16 4.2 4.2" />
              </svg>
              {t.searchDriver}
            </a>
            <a className="landing-button landing-button-secondary" href="#how-it-works">
              {t.explore} <span aria-hidden="true">↗</span>
            </a>
          </div>

        </div>

      </section>

      <section className="landing-trust-section" id="how-it-works" aria-labelledby="trust-title">
        <div className="landing-hero-visual" aria-label="Illustration of driver verification information">
          <div className="visual-orbit visual-orbit-one" />
          <div className="visual-orbit visual-orbit-two" />
          <div className="visual-glow" />
          <div className="visual-card visual-card-main">
            <div className="visual-card-top">
              <span className="visual-card-label">{t.visualLabel}</span>
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
                <strong>{t.profile}</strong>
                <span>{t.qualifications}</span>
              </div>
            </div>
            <div className="visual-divider" />
            <div className="visual-status-row">
              <span className="visual-status-icon" aria-hidden="true">✓</span>
              <div><strong>{t.identityReview}</strong><span>{t.statusAvailable}</span></div>
              <span className="visual-status-label">{t.status}</span>
            </div>
            <div className="visual-status-row">
              <span className="visual-status-icon visual-status-icon-blue" aria-hidden="true">↗</span>
              <div><strong>{t.licenceInfo}</strong><span>{t.validatedDetails}</span></div>
              <span className="visual-status-label">{t.status}</span>
            </div>
            <div className="visual-score-panel">
              <div><span>{t.performanceInsights}</span><strong>{t.clearFairTraceable}</strong></div>
              <div className="visual-score-bars" aria-hidden="true"><i /><i /><i /><i /><i /></div>
            </div>
            <p className="visual-disclaimer">{t.illustrativePreview}</p>
          </div>
          <div className="visual-floating-badge">
            <span aria-hidden="true">✦</span>
            {t.builtAroundTrust}
          </div>
        </div>
        <div className="landing-section-heading">
          <p className="landing-eyebrow">{t.trustEyebrow}</p>
          <h2 id="trust-title">{t.trustTitle}</h2>
          <p>{t.trustIntro}</p>
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
          {t.integrationNote}
        </p>
      </section>

      <section className="landing-start-section" id="get-started" aria-labelledby="start-title">
        <div className="landing-start-intro">
          <p className="landing-eyebrow">{t.startEyebrow}</p>
          <h2 id="start-title">{t.startTitle}</h2>
          <p>{t.startIntro}</p>
        </div>
        <div className="landing-audience-grid">
          <article className="landing-audience-card">
            <div className="landing-audience-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M5 17h14l-1.5-7h-11L5 17Z" /><path d="m8 10 1-4h6l1 4M7 17v2m10-2v2M7 14h.01M17 14h.01" /></svg>
            </div>
            <p className="landing-audience-label">{t.driverLabel}</p>
            <h3>{t.driverTitle}</h3>
            <p>{t.driverCopy}</p>
            <Link className="landing-text-link" href="/driver/onboarding">{t.joinDriver} <span aria-hidden="true">→</span></Link>
          </article>
          <article className="landing-audience-card landing-audience-card-featured">
            <div className="landing-audience-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M3 20h18M5 20V8l7-4 7 4v12M9 20v-5h6v5M9 10h.01M15 10h.01" /></svg>
            </div>
            <p className="landing-audience-label">{t.clientLabel}</p>
            <h3>{t.clientTitle}</h3>
            <p>{t.clientCopy}</p>
            <Link className="landing-text-link" href="#get-started">{t.findDriver} <span aria-hidden="true">→</span></Link>
          </article>
        </div>
        <p className="landing-existing-account">{t.existingAccount} <Link href="/sign-in">{t.loginHere}</Link></p>
      </section>

      <footer className="landing-footer">
        <Link className="landing-footer-brand" href="/">
          <span className="landing-brand-mark" aria-hidden="true">D</span>
          <span>DIVS</span>
        </Link>
        <p>{t.footerDescriptor}</p>
        <a href="#landing-hero-title">{t.backToTop} ↑</a>
        <small>© {new Date().getFullYear()} DIVS. {t.footerCopyright}</small>
      </footer>
    </main>
  );
}
