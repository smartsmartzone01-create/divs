import { AuthShell } from "@/features/identity/components/auth-shell";
import { VerifyForm } from "@/features/identity/components/verify-form";

type VerifyPageProps = {
  searchParams: Promise<{ channel?: string | string[]; target?: string | string[] }>;
};

export default async function VerifyPage({ searchParams }: VerifyPageProps) {
  const params = await searchParams;
  const channelValue = Array.isArray(params.channel) ? params.channel[0] : params.channel;
  const targetValue = Array.isArray(params.target) ? params.target[0] : params.target;

  return (
    <AuthShell
      eyebrow="Verify your contact"
      title="Confirm it belongs to you."
      description="Request a short-lived code, then enter it here. A contact is not marked verified until DIVS confirms the code."
    >
      <VerifyForm
        initialChannel={channelValue === "phone" ? "phone" : "email"}
        initialTarget={targetValue ?? ""}
      />
    </AuthShell>
  );
}
