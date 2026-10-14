import { AuthShell } from "@/features/identity/components/auth-shell";
import { PasswordResetForm } from "@/features/identity/components/password-reset-form";

export default function ForgotPasswordPage() {
  return (
    <AuthShell
      eyebrow="Account recovery"
      title="Reset your password."
      description="Use a verified email address or phone number. DIVS will not reveal whether an account exists."
    >
      <PasswordResetForm />
    </AuthShell>
  );
}
