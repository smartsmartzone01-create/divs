"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentAccount, getDriverRegistration, submitDriverRegistration, type AuthAccount, type DriverRegistration } from "@/features/identity/api";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";
import { TANZANIA_DISTRICTS, TANZANIA_REGIONS } from "@/features/identity/data/tanzania-administrative-divisions";

const experienceOptions = [
  ["none", "No professional driving experience", "Sina uzoefu wa kitaalamu wa udereva"],
  ["under_1_year", "Less than 1 year", "Chini ya mwaka 1"],
  ["1_to_3_years", "1–3 years", "Miaka 1–3"],
  ["4_to_7_years", "4–7 years", "Miaka 4–7"],
  ["8_plus_years", "8 or more years", "Miaka 8 au zaidi"],
] as const;

const steps = [
  { en: "Personal", sw: "Binafsi" },
  { en: "Location", sw: "Makazi" },
  { en: "Experience", sw: "Uzoefu" },
  { en: "Review", sw: "Kagua" },
] as const;

type FormState = {
  first_name: string;
  middle_name: string;
  last_name: string;
  nationality: string;
  region: string;
  district: string;
  residential_area: string;
  current_residential_address: string;
  driving_experience: DriverRegistration["driving_experience"];
};

const initialForm: FormState = {
  first_name: "",
  middle_name: "",
  last_name: "",
  nationality: "Tanzanian",
  region: "",
  district: "",
  residential_area: "",
  current_residential_address: "",
  driving_experience: "none",
};

export function DriverOnboardingForm() {
  const router = useRouter();
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  const [account, setAccount] = useState<AuthAccount | null>(null);
  const [existing, setExisting] = useState<DriverRegistration | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [form, setForm] = useState<FormState>(initialForm);

  const districts = useMemo(() => form.region ? TANZANIA_DISTRICTS[form.region] ?? [] : [], [form.region]);

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

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({
      ...current,
      [key]: value,
      ...(key === "region" ? { district: "" } : {}),
    }));
  }

  function validateStep(currentStep: number) {
    if (currentStep === 0 && (!form.first_name.trim() || !form.last_name.trim() || !form.nationality.trim())) {
      return sw ? "Jaza jina la kwanza, jina la mwisho na uraia ili kuendelea." : "Enter your first name, last name and nationality to continue.";
    }
    if (currentStep === 1 && (!form.region || !form.district || !form.current_residential_address.trim())) {
      return sw ? "Chagua mkoa na wilaya, kisha jaza anwani yako ya makazi." : "Choose your region and district, then enter your current residential address.";
    }
    return "";
  }

  function continueStep() {
    const message = validateStep(step);
    if (message) {
      setError(message);
      return;
    }
    setError("");
    setStep((current) => Math.min(current + 1, steps.length - 1));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = validateStep(0) || validateStep(1);
    if (message) {
      setError(message);
      setStep(!form.first_name.trim() || !form.last_name.trim() || !form.nationality.trim() ? 0 : 1);
      return;
    }
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
        <p>{sw ? "Taarifa zako za awali zimehifadhiwa. Hii haimaanishi kuwa umethibitishwa. Uhakiki utasubiri hadi njia rasmi za uhakiki ziwekwe na kukamilishwa." : "Your initial details are saved. This does not mean you are verified. Verification remains pending until the official review methods are configured and completed."}</p>
        <div className="driver-onboarding-status-row"><span>{sw ? "Hali ya uhakiki" : "Verification status"}</span><strong>{sw ? "Inasubiri" : "Pending"}</strong></div>
        <div className="driver-onboarding-status-row"><span>{sw ? "Akaunti" : "Account"}</span><strong>{account?.email || account?.phone_number}</strong></div>
        <p className="auth-helper">{sw ? "Nafasi ya dereva itapatikana katika hatua inayofuata ya DIVS." : "Your dedicated Driver Workspace will be introduced in the next phase."}</p>
        <button className="auth-primary-button" type="button" onClick={() => router.push("/account")}>{sw ? "Rudi kwenye akaunti" : "Return to account"}</button>
      </section>
    );
  }

  const fullName = [form.first_name, form.middle_name, form.last_name].filter(Boolean).join(" ");
  const selectedExperience = experienceOptions.find(([value]) => value === form.driving_experience);
  const stepTitle = [
    sw ? "Taarifa binafsi" : "Personal information",
    sw ? "Mahali unapoishi" : "Where you live",
    sw ? "Uzoefu wa udereva" : "Driving experience",
    sw ? "Kagua taarifa zako" : "Review your information",
  ][step];

  return (
    <form className="auth-form driver-onboarding-form" onSubmit={handleSubmit}>
      <div className="driver-step-progress" aria-label={sw ? `Hatua ya ${step + 1} kati ya 4` : `Step ${step + 1} of 4`}>
        <div className="driver-step-progress-labels">
          {steps.map((item, index) => (
            <div className={`driver-step-label ${index < step ? "is-complete" : ""} ${index === step ? "is-current" : ""}`} key={item.en}>
              <span className="driver-step-label-dot">{index < step ? "✓" : index + 1}</span>
              <span>{sw ? item.sw : item.en}</span>
            </div>
          ))}
        </div>
        <div className="driver-step-track"><span style={{ width: `${(step / (steps.length - 1)) * 100}%` }} /></div>
      </div>

      <div className="driver-onboarding-section-heading">
        <p className="driver-step-kicker">{sw ? `HATUA ${step + 1} YA 4` : `STEP ${step + 1} OF 4`}</p>
        <h2>{stepTitle}</h2>
        <p>{[
          sw ? "Tumia majina yako kama yalivyo kwenye nyaraka zako rasmi." : "Enter your names as they appear on your official documents.",
          sw ? "Chagua mkoa na wilaya unayoishi kwa sasa." : "Select the region and district where you currently live.",
          sw ? "Chagua kiwango kinachoelezea uzoefu wako wa udereva." : "Choose the option that best describes your driving experience.",
          sw ? "Kagua taarifa zote kabla ya kutuma usajili wako." : "Check that everything is correct before submitting your registration.",
        ][step]}</p>
      </div>

      {step === 0 ? (
        <div className="driver-onboarding-field-grid">
          <div className="auth-field"><label htmlFor="driver-first-name">{sw ? "Jina la kwanza *" : "First name *"}</label><input id="driver-first-name" required maxLength={100} value={form.first_name} onChange={(e) => update("first_name", e.target.value)} autoComplete="given-name" /></div>
          <div className="auth-field"><label htmlFor="driver-middle-name">{sw ? "Jina la kati (hiari)" : "Middle name (optional)"}</label><input id="driver-middle-name" maxLength={100} value={form.middle_name} onChange={(e) => update("middle_name", e.target.value)} autoComplete="additional-name" /></div>
          <div className="auth-field"><label htmlFor="driver-last-name">{sw ? "Jina la mwisho *" : "Last name *"}</label><input id="driver-last-name" required maxLength={100} value={form.last_name} onChange={(e) => update("last_name", e.target.value)} autoComplete="family-name" /></div>
          <div className="auth-field"><label htmlFor="driver-nationality">{sw ? "Uraia *" : "Nationality *"}</label><input id="driver-nationality" required maxLength={100} value={form.nationality} onChange={(e) => update("nationality", e.target.value)} /></div>
        </div>
      ) : null}

      {step === 1 ? (
        <div className="driver-onboarding-field-grid">
          <div className="auth-field"><label htmlFor="driver-country">{sw ? "Nchi" : "Country"}</label><input id="driver-country" value="Tanzania" readOnly aria-readonly="true" /></div>
          <div className="auth-field"><label htmlFor="driver-region">{sw ? "Mkoa *" : "Region *"}</label><select id="driver-region" required value={form.region} onChange={(e) => update("region", e.target.value)} autoComplete="address-level1"><option value="">{sw ? "Chagua mkoa" : "Select a region"}</option>{TANZANIA_REGIONS.map((region) => <option key={region} value={region}>{region}</option>)}</select></div>
          <div className="auth-field"><label htmlFor="driver-district">{sw ? "Wilaya *" : "District *"}</label><select id="driver-district" required value={form.district} onChange={(e) => update("district", e.target.value)} disabled={!form.region} autoComplete="address-level2"><option value="">{sw ? "Chagua wilaya" : "Select a district"}</option>{districts.map((district) => <option key={district} value={district}>{district}</option>)}</select></div>
          <div className="auth-field"><label htmlFor="driver-area">{sw ? "Eneo / Kata (hiari)" : "Residential area / ward (optional)"}</label><input id="driver-area" maxLength={120} value={form.residential_area} onChange={(e) => update("residential_area", e.target.value)} /></div>
          <div className="auth-field driver-onboarding-full"><label htmlFor="driver-address">{sw ? "Maelezo ya mahali unapoishi *" : "Current residential address *"}</label><textarea id="driver-address" required rows={3} value={form.current_residential_address} onChange={(e) => update("current_residential_address", e.target.value)} placeholder={sw ? "Mfano: Mtaa, kata, karibu na eneo maarufu" : "For example: street, ward, and a nearby landmark"} /></div>
        </div>
      ) : null}

      {step === 2 ? (
        <div className="driver-experience-options">
          {experienceOptions.map(([value, en, swLabel]) => (
            <label className={`driver-experience-option ${form.driving_experience === value ? "is-selected" : ""}`} key={value}>
              <input type="radio" name="driving_experience" value={value} checked={form.driving_experience === value} onChange={() => update("driving_experience", value)} />
              <span className="driver-experience-radio" aria-hidden="true" />
              <span>{sw ? swLabel : en}</span>
            </label>
          ))}
        </div>
      ) : null}

      {step === 3 ? (
        <div className="driver-review-list">
          <section><div><h3>{sw ? "Taarifa binafsi" : "Personal information"}</h3><button type="button" onClick={() => setStep(0)}>{sw ? "Hariri" : "Edit"}</button></div><dl><dt>{sw ? "Jina kamili" : "Full name"}</dt><dd>{fullName}</dd><dt>{sw ? "Uraia" : "Nationality"}</dt><dd>{form.nationality}</dd></dl></section>
          <section><div><h3>{sw ? "Mahali unapoishi" : "Residential location"}</h3><button type="button" onClick={() => setStep(1)}>{sw ? "Hariri" : "Edit"}</button></div><dl><dt>{sw ? "Nchi" : "Country"}</dt><dd>Tanzania</dd><dt>{sw ? "Mkoa" : "Region"}</dt><dd>{form.region}</dd><dt>{sw ? "Wilaya" : "District"}</dt><dd>{form.district}</dd><dt>{sw ? "Eneo / Kata" : "Area / ward"}</dt><dd>{form.residential_area || "—"}</dd><dt>{sw ? "Anwani" : "Address"}</dt><dd>{form.current_residential_address}</dd></dl></section>
          <section><div><h3>{sw ? "Uzoefu" : "Driving experience"}</h3><button type="button" onClick={() => setStep(2)}>{sw ? "Hariri" : "Edit"}</button></div><p>{sw ? selectedExperience?.[2] : selectedExperience?.[1]}</p></section>
          <div className="driver-onboarding-account-note"><strong>{sw ? "Mawasiliano ya akaunti" : "Account contact details"}</strong><span>{account?.email || account?.phone_number || "—"}</span><p>{sw ? "Mawasiliano haya yameunganishwa na akaunti yako." : "These contact details are linked to your account."}</p></div>
          <p className="driver-onboarding-disclaimer">{sw ? "Kutuma taarifa hizi kunaunda wasifu wa awali tu. Hakuna taarifa ya utambulisho, leseni au rekodi za polisi inayohesabiwa kuwa imehakikiwa kwa hatua hii." : "Submitting creates an initial profile only. Identity, licence and police records are not verified by this registration."}</p>
        </div>
      ) : null}

      {error ? <p className="auth-error" role="alert">{error}</p> : null}
      <div className="driver-step-actions">
        {step > 0 ? <button className="auth-secondary-button" type="button" onClick={() => { setError(""); setStep((current) => current - 1); }}>{sw ? "Rudi nyuma" : "Back"}</button> : <span />}
        {step < steps.length - 1 ? (
          <button className="auth-primary-button" type="button" onClick={continueStep}>{sw ? "Endelea" : "Continue"} <span aria-hidden="true">→</span></button>
        ) : (
          <button className="auth-primary-button" type="submit" disabled={busy}>{busy ? (sw ? "Inatuma…" : "Submitting…") : (sw ? "Tuma usajili" : "Submit registration")}</button>
        )}
      </div>
    </form>
  );
}
