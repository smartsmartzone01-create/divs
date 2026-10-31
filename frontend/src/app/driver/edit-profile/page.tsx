"use client";

import Link from "next/link";
import { AuthShell } from "@/features/identity/components/auth-shell";
import { DriverOnboardingForm } from "@/features/identity/components/driver-onboarding-form";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";

export default function DriverEditProfilePage() {
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  return (
    <AuthShell
      eyebrow={sw ? "TAARIFA ZA DEREVA" : "DRIVER PROFILE"}
      title={sw ? "Hariri wasifu wako" : "Edit your profile"}
      description={sw ? "Sasisha taarifa zako za msingi za dereva." : "Update your driver's personal and residential information."}
      footer={<span>{sw ? "Umemaliza?" : "Finished editing?"} <Link href="/workspace/driver">{sw ? "Rudi kwenye nafasi yako" : "Return to your workspace"}</Link></span>}
    >
      <DriverOnboardingForm allowEdit />
    </AuthShell>
  );
}
