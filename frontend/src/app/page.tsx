export default function HomePage() {
  return (
    <main className="page-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="DIVS home">
          <span className="brand-mark" aria-hidden="true">
            D
          </span>
          <span>DIVS</span>
        </a>
        <span className="header-note">Driver Identification &amp; Verification</span>
      </header>

      <section className="hero" aria-labelledby="hero-title">
        <p className="eyebrow">A trusted way to find professional drivers</p>
        <h1 id="hero-title">Find the right driver with confidence.</h1>
        <p className="hero-copy">
          Explore driver profiles, verified driving qualifications, and
          performance information in one place.
        </p>
        <div className="home-actions">
          <a className="home-primary-link" href="/register">Create an account</a>
          <a className="home-secondary-link" href="/sign-in">Sign in</a>
        </div>
        <p className="setup-note">
          Frontend foundation is ready. Public discovery will connect to the
          Django API as the interface is built.
        </p>
      </section>

      <footer className="site-footer">
        <span>DIVS</span>
        <span>Driver information handled with care.</span>
      </footer>
    </main>
  );
}
