import { AuthShell } from "@/features/identity/components/auth-shell";
import { AccountPanel } from "@/features/identity/components/account-panel";

export default function AccountPage() {
  return (
    <AuthShell
      eyebrow="Your identity"
      title="Account and sessions."
      description="Review your verified contact methods and manage the devices currently signed in to DIVS."
    >
      <AccountPanel />
    </AuthShell>
  );
}
