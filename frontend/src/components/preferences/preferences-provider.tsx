"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type DIVSLanguage = "en" | "sw";
export type DIVSTheme = "light" | "dark";

const messages = {
  en: {
    navHow: "How it works",
    navVerification: "Verification",
    navGetStarted: "Get started",
    login: "Log in",
    createAccount: "Create account",
    languageLabel: "Language",
    themeToDark: "Switch to dark mode",
    themeToLight: "Switch to light mode",
    eyebrow: "A clearer way to choose a driver",
    heroLineOne: "Find the right driver.",
    heroLineTwo: "Hire with confidence.",
    heroCopy: "Discover professional drivers, review their verified qualifications, and make more informed hiring decisions — all in one place.",
    searchDriver: "Search for a driver",
    explore: "Explore DIVS",
    heroNote: "Verification status is shown transparently, based on available evidence.",
    visualLabel: "DIVS VERIFICATION",
    profile: "Driver profile",
    qualifications: "Qualifications & records",
    identityReview: "Identity review",
    statusAvailable: "Status available when reviewed",
    licenceInfo: "Licence information",
    validatedDetails: "Validated details",
    status: "Status",
    performanceInsights: "Performance insights",
    clearFairTraceable: "Clear. Fair. Traceable.",
    illustrativePreview: "Illustrative preview · not a live verification record",
    builtAroundTrust: "Built around trust",
    identify: "IDENTIFY",
    verify: "VERIFY",
    discover: "DISCOVER",
    trustEyebrow: "Confidence through clarity",
    trustTitle: "More than a name on a list.",
    trustIntro: "Useful information to help people and businesses make better-informed driver hiring decisions.",
    benefitOneTitle: "Verified qualifications",
    benefitOneCopy: "See clear verification statuses and licence information validated through the available review process.",
    benefitTwoTitle: "Performance insights",
    benefitTwoCopy: "Understand a driver's performance history and the reasons behind changes to their score.",
    benefitThreeTitle: "A more responsible process",
    benefitThreeCopy: "Designed for authorized verification integrations, with manual review where required.",
    integrationNote: "Government verification integrations will be described as connected only when authorized services are live. Manual review may be used where available.",
    startEyebrow: "Your next step",
    startTitle: "What brings you to DIVS?",
    startIntro: "Choose how you want to get started. You can explore public information before creating an account.",
    driverLabel: "FOR DRIVERS",
    driverTitle: "Build your professional profile.",
    driverCopy: "Register, complete your profile, and follow your verification progress.",
    joinDriver: "Join as a driver",
    clientLabel: "FOR CLIENTS & BUSINESSES",
    clientTitle: "Find a driver for your needs.",
    clientCopy: "Explore drivers and use verified information to support your hiring decision.",
    findDriver: "Find a driver",
    existingAccount: "Already have an account?",
    loginHere: "Log in here",
    footerDescriptor: "Driver Identification & Verification System",
    backToTop: "Back to top",
    footerCopyright: "Built for more informed decisions.",
    openMenu: "Open navigation menu",
    closeMenu: "Close navigation menu",
  },
  sw: {
    navHow: "Jinsi inavyofanya kazi",
    navVerification: "Uhakiki",
    navGetStarted: "Anza hapa",
    login: "Ingia",
    createAccount: "Fungua akaunti",
    languageLabel: "Lugha",
    themeToDark: "Washa hali ya giza",
    themeToLight: "Washa hali ya mwanga",
    eyebrow: "Njia bora ya kuchagua dereva",
    heroLineOne: "Pata dereva anayekufaa.",
    heroLineTwo: "Ajiri kwa kujiamini.",
    heroCopy: "Gundua madereva wa kitaalamu, kagua sifa zao zilizohakikiwa, na ufanye maamuzi bora ya kuajiri — sehemu moja.",
    searchDriver: "Tafuta dereva",
    explore: "Fahamu DIVS",
    heroNote: "Hali ya uhakiki huonyeshwa wazi kulingana na ushahidi unaopatikana.",
    visualLabel: "UHAKIKI WA DIVS",
    profile: "Wasifu wa dereva",
    qualifications: "Sifa na rekodi",
    identityReview: "Uhakiki wa utambulisho",
    statusAvailable: "Hali itaonyeshwa baada ya uhakiki",
    licenceInfo: "Taarifa za leseni",
    validatedDetails: "Taarifa zilizothibitishwa",
    status: "Hali",
    performanceInsights: "Taarifa za utendaji",
    clearFairTraceable: "Wazi. Haki. Unaofuatilika.",
    illustrativePreview: "Mfano wa mwonekano · si rekodi halisi ya uhakiki",
    builtAroundTrust: "Imejengwa kwa kuzingatia uaminifu",
    identify: "TAMBUA",
    verify: "HAKIKI",
    discover: "GUNDUA",
    trustEyebrow: "Uaminifu kupitia uwazi",
    trustTitle: "Zaidi ya jina kwenye orodha.",
    trustIntro: "Taarifa muhimu zinazowasaidia watu na biashara kufanya maamuzi bora ya kuajiri madereva.",
    benefitOneTitle: "Sifa zilizohakikiwa",
    benefitOneCopy: "Ona hali ya uhakiki na taarifa za leseni zilizokaguliwa kupitia mchakato unaopatikana.",
    benefitTwoTitle: "Taarifa za utendaji",
    benefitTwoCopy: "Elewa historia ya utendaji wa dereva na sababu za mabadiliko ya alama yake.",
    benefitThreeTitle: "Mchakato unaowajibika",
    benefitThreeCopy: "Imeandaliwa kwa miunganisho ya uhakiki iliyoidhinishwa, pamoja na ukaguzi wa mikono inapohitajika.",
    integrationNote: "Miunganisho ya uhakiki wa serikali itaelezwa kuwa imeunganishwa tu huduma zilizoidhinishwa zitakapokuwa zinafanya kazi. Ukaguzi wa mikono unaweza kutumika pale unapopatikana.",
    startEyebrow: "Hatua yako inayofuata",
    startTitle: "Umekuja DIVS kwa sababu gani?",
    startIntro: "Chagua jinsi ya kuanza. Unaweza kuchunguza taarifa za umma kabla ya kufungua akaunti.",
    driverLabel: "KWA MADEREVA",
    driverTitle: "Jenga wasifu wako wa kitaalamu.",
    driverCopy: "Jisajili, kamilisha wasifu wako, na fuatilia maendeleo ya uhakiki.",
    joinDriver: "Jisajili kama dereva",
    clientLabel: "KWA WATEJA NA BIASHARA",
    clientTitle: "Tafuta dereva kwa mahitaji yako.",
    clientCopy: "Chunguza madereva na tumia taarifa zilizohakikiwa kusaidia uamuzi wako wa kuajiri.",
    findDriver: "Tafuta dereva",
    existingAccount: "Tayari una akaunti?",
    loginHere: "Ingia hapa",
    footerDescriptor: "Mfumo wa Utambuzi na Uhakiki wa Madereva",
    backToTop: "Rudi juu",
    footerCopyright: "Kwa maamuzi yenye taarifa bora zaidi.",
    openMenu: "Fungua menyu ya urambazaji",
    closeMenu: "Funga menyu ya urambazaji",
  },
} as const;

type Messages = { [Key in keyof (typeof messages)["en"]]: string };

type PreferencesContextValue = {
  language: DIVSLanguage;
  theme: DIVSTheme;
  setLanguage: (language: DIVSLanguage) => void;
  toggleTheme: () => void;
  t: Messages;
};

const PreferencesContext = createContext<PreferencesContextValue | null>(null);

export function DIVSPreferencesProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<DIVSLanguage>("en");
  const [theme, setThemeState] = useState<DIVSTheme>("light");
  const [preferencesLoaded, setPreferencesLoaded] = useState(false);

  useEffect(() => {
    const savedLanguage = window.localStorage.getItem("divs-language");
    const savedTheme = window.localStorage.getItem("divs-theme");
    if (savedLanguage === "en" || savedLanguage === "sw") {
      setLanguageState(savedLanguage);
    }
    if (savedTheme === "light" || savedTheme === "dark") {
      setThemeState(savedTheme);
    }
    setPreferencesLoaded(true);
  }, []);

  useEffect(() => {
    if (!preferencesLoaded) return;
    document.documentElement.lang = language;
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    window.localStorage.setItem("divs-language", language);
    window.localStorage.setItem("divs-theme", theme);
  }, [language, theme, preferencesLoaded]);

  const setLanguage = useCallback((nextLanguage: DIVSLanguage) => {
    setLanguageState(nextLanguage);
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState((current) => (current === "light" ? "dark" : "light"));
  }, []);

  const value = useMemo(
    () => ({ language, theme, setLanguage, toggleTheme, t: messages[language] }),
    [language, theme, setLanguage, toggleTheme],
  );

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}

export function useDIVSPreferences() {
  const context = useContext(PreferencesContext);
  if (!context) {
    throw new Error("useDIVSPreferences must be used inside DIVSPreferencesProvider");
  }
  return context;
}
