"use client";

import Link from "next/link";
import { AuthShell } from "@/features/identity/components/auth-shell";
import { DriverOnboardingForm } from "@/features/identity/components/driver-onboarding-form";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";

export default function DriverOnboardingPage() {
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  return (
    <AuthShell
      eyebrow={sw ? "USAJILI WA DEREVA" : "DRIVER ONBOARDING"}
      title={sw ? "Jenga wasifu wako wa dereva" : "Set up your driver profile"}
      description={sw ? "Kamilisha taarifa zako za msingi ili kuunda wasifu wako wa DIVS. Uhakiki ni hatua tofauti na bado haujawezeshwa." : "Complete your initial details to create your DIVS driver profile. Verification is a separate step and is not enabled yet."}
      footer={<span>{sw ? "Si dereva?" : "Not registering as a driver?"} <Link href="/">{sw ? "Rudi mwanzo" : "Return home"}</Link></span>}
    >
      <DriverOnboardingForm />
    </AuthShell>
  );
}
