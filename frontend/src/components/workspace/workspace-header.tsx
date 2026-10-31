"use client";

import Link from "next/link";
import { useState } from "react";
import { UserAccountMenu } from "@/features/identity/components/user-account-menu";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";

export function WorkspaceHeader() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { language, setLanguage, theme, toggleTheme } = useDIVSPreferences();

  return (
    <header className="workspace-header">
      <div className="workspace-header-inner">
        <Link href="/" className="workspace-brand" aria-label="DIVS home">
          <span className="workspace-brand-mark">D</span><span>DIVS</span>
        </Link>
        <div className="workspace-header-actions">
          <button type="button" className="workspace-menu-toggle" aria-label={menuOpen ? "Close workspace menu" : "Open workspace menu"} aria-expanded={menuOpen} aria-controls="workspace-navigation" onClick={() => setMenuOpen((open) => !open)}>
            <span /><span /><span />
          </button>
          <UserAccountMenu />
        </div>
        <nav id="workspace-navigation" className={"workspace-navigation" + (menuOpen ? " is-open" : "")} aria-label="Workspace navigation">
          <Link href="/workspace/admin" onClick={() => setMenuOpen(false)}>{language === "sw" ? "Dashibodi" : "Workspace"}</Link>
          <Link href="/account" onClick={() => setMenuOpen(false)}>{language === "sw" ? "Akaunti na vipindi" : "Account & sessions"}</Link>
          <div className="workspace-preferences">
            <button type="button" onClick={() => setLanguage(language === "en" ? "sw" : "en")} aria-label="Change language">{language === "en" ? "SW" : "EN"}</button>
            <button type="button" onClick={toggleTheme} aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}>{theme === "light" ? "Dark" : "Light"}</button>
          </div>
        </nav>
      </div>
    </header>
  );
}
