"use client";

import { type FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentAccount, getDriverRegistration, submitDriverRegistration, type AuthAccount, type DriverRegistration } from "@/features/identity/api";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";

const experienceOptions = [
  ["none", "No professional driving experience", "Sina uzoefu wa kitaalamu wa udereva"],
  ["under_1_year", "Less than 1 year", "Chini ya mwaka 1"],
  ["1_to_3_years", "1–3 years", "Miaka 1–3"],
  ["4_to_7_years", "4–7 years", "Miaka 4–7"],
  ["8_plus_years", "8 or more years", "Miaka 8 au zaidi"],
] as const;

export function DriverOnboardingForm() {
  const router = useRouter();
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  const [account, setAccount] = useState<AuthAccount | null>(null);
  const [existing, setExisting] = useState<DriverRegistration | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    first_name: "",
    middle_name: "",
    last_name: "",
    nationality: "Tanzanian",
    region: "",
    district: "",
    residential_area: "",
    current_residential_address: "",
    driving_experience: "none" as DriverRegistration["driving_experience"],
  });

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const current = await getCurrentAccount();
        if (!active) return;
        setAccount(current);
        try {
          const registration = await getDriverRegistration();
          if (!active) return;
          if (registration) {
            setExisting(registration);
            setForm({
              first_name: registration.first_name,
              middle_name: registration.middle_name,
              last_name: registration.last_name,
              nationality: registration.nationality,
              region: registration.region,
              district: registration.district,
              residential_area: registration.residential_area,
              current_residential_address: registration.current_residential_address,
              driving_experience: registration.driving_experience,
            });
          }
        } catch (caught) {
          if (active) setError(caught instanceof Error ? caught.message : "Could not load your driver registration.");
        }
      } catch {
        if (active) router.replace("/sign-in?next=%2Fdriver%2Fonboarding");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [router]);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const saved = await submitDriverRegistration(form);
      setExisting(saved);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : (sw ? "Usajili haukufanikiwa. Jaribu tena." : "Registration failed. Please try again."));
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <p className="auth-helper">{sw ? "Inapakia taarifa za akaunti…" : "Loading your account…"}</p>;

  if (existing) {
    return (
      <section className="driver-onboarding-success" aria-live="polite">
        <div className="driver-onboarding-success-icon" aria-hidden="true">✓</div>
        <p className="driver-onboarding-status">{sw ? "USAJILI UMEPOKELEWA" : "REGISTRATION RECEIVED"}</p>
        <h2>{sw ? "Wasifu wako wa dereva umeundwa" : "Your driver profile has been created"}</h2>
        <p>{sw ? "Taarifa zako za awali zimehifadhiwa. Hii haimaanishi kuwa umethibitishwa. Uhakiki utasubiri hadi njia rasmi za uhakiki ziwekwe na kukamilishwa." : "Your initial details are saved. This does not mean you are verified. Verification will remain pending until the official review methods are configured and completed."}</p>
        <div className="driver-onboarding-status-row"><span>{sw ? "Hali ya uhakiki" : "Verification status"}</span><strong>{sw ? "Inasubiri" : "Pending"}</strong></div>
        <div className="driver-onboarding-status-row"><span>{sw ? "Akaunti" : "Account"}</span><strong>{account?.email || account?.phone_number}</strong></div>
        <p className="auth-helper">{sw ? "Taarifa za wasifu zinaweza kuhaririwa katika hatua inayofuata ya nafasi ya dereva." : "Profile editing will be available in the next Driver Workspace phase."}</p>
        <button className="auth-primary-button" type="button" onClick={() => router.push("/account")}>{sw ? "Rudi kwenye akaunti" : "Return to account"}</button>
      </section>
    );
  }

  return (
    <form className="auth-form driver-onboarding-form" onSubmit={handleSubmit}>
      <div className="driver-onboarding-section-heading">
        <h2>{sw ? "Taarifa binafsi" : "Personal information"}</h2>
        <p>{sw ? "Tumia majina yako kama yalivyo kwenye nyaraka zako rasmi." : "Enter your names as they appear on your official documents."}</p>
      </div>
      <div className="driver-onboarding-field-grid">
        <div className="auth-field"><label htmlFor="driver-first-name">{sw ? "Jina la kwanza *" : "First name *"}</label><input id="driver-first-name" required maxLength={100} value={form.first_name} onChange={(e) => update("first_name", e.target.value)} autoComplete="given-name" /></div>
        <div className="auth-field"><label htmlFor="driver-middle-name">{sw ? "Jina la kati (hiari)" : "Middle name (optional)"}</label><input id="driver-middle-name" maxLength={100} value={form.middle_name} onChange={(e) => update("middle_name", e.target.value)} autoComplete="additional-name" /></div>
        <div className="auth-field"><label htmlFor="driver-last-name">{sw ? "Jina la mwisho *" : "Last name *"}</label><input id="driver-last-name" required maxLength={100} value={form.last_name} onChange={(e) => update("last_name", e.target.value)} autoComplete="family-name" /></div>
        <div className="auth-field"><label htmlFor="driver-nationality">{sw ? "Uraia *" : "Nationality *"}</label><input id="driver-nationality" required maxLength={100} value={form.nationality} onChange={(e) => update("nationality", e.target.value)} /></div>
      </div>

      <div className="driver-onboarding-section-heading"><h2>{sw ? "Mahali unapoishi" : "Where you live"}</h2><p>{sw ? "Taarifa hizi zitasaidia kuweka eneo lako la huduma." : "This helps establish your service area."}</p></div>
      <div className="driver-onboarding-field-grid">
        <div className="auth-field"><label htmlFor="driver-region">{sw ? "Mkoa *" : "Region *"}</label><input id="driver-region" required maxLength={120} value={form.region} onChange={(e) => update("region", e.target.value)} autoComplete="address-level1" /></div>
        <div className="auth-field"><label htmlFor="driver-district">{sw ? "Wilaya *" : "District *"}</label><input id="driver-district" required maxLength={120} value={form.district} onChange={(e) => update("district", e.target.value)} autoComplete="address-level2" /></div>
        <div className="auth-field"><label htmlFor="driver-area">{sw ? "Eneo / Kata (hiari)" : "Residential area / ward (optional)"}</label><input id="driver-area" maxLength={120} value={form.residential_area} onChange={(e) => update("residential_area", e.target.value)} /></div>
        <div className="auth-field driver-onboarding-full"><label htmlFor="driver-address">{sw ? "Maelezo ya mahali unapoishi *" : "Current residential address *"}</label><textarea id="driver-address" required rows={3} value={form.current_residential_address} onChange={(e) => update("current_residential_address", e.target.value)} placeholder={sw ? "Eleza eneo lako la makazi" : "Describe your current residential location"} /></div>
      </div>

      <div className="driver-onboarding-section-heading"><h2>{sw ? "Uzoefu wa udereva" : "Driving experience"}</h2><p>{sw ? "Chagua kiwango kinachokuelezea kwa usahihi." : "Choose the option that best describes your experience."}</p></div>
      <div className="auth-field"><label htmlFor="driver-experience">{sw ? "Uzoefu *" : "Experience *"}</label><select id="driver-experience" required value={form.driving_experience} onChange={(e) => update("driving_experience", e.target.value as DriverRegistration["driving_experience"])}>{experienceOptions.map(([value, en, swLabel]) => <option key={value} value={value}>{sw ? swLabel : en}</option>)}</select></div>

      <div className="driver-onboarding-account-note"><strong>{sw ? "Mawasiliano ya akaunti" : "Account contact details"}</strong><span>{account?.email || account?.phone_number || "—"}</span><p>{sw ? "Mawasiliano haya yameunganishwa na akaunti yako na hayawezi kubadilishwa hapa." : "These details are linked to your account and cannot be changed in this form."}</p></div>
      <p className="driver-onboarding-disclaimer">{sw ? "Kutuma taarifa hizi kunaunda wasifu wa awali tu. Hakuna leseni, utambulisho au rekodi za polisi zitakazochukuliwa kuwa zimehakikiwa kwa hatua hii." : "Submitting these details creates an initial profile only. No licence, identity or police record is treated as verified at this stage."}</p>
      {error && <p className="auth-error" role="alert">{error}</p>}
      <button className="auth-primary-button" type="submit" disabled={busy}>{busy ? (sw ? "Inatuma…" : "Submitting…") : (sw ? "Tuma usajili wa dereva" : "Submit driver registration")}</button>
    </form>
  );
}
