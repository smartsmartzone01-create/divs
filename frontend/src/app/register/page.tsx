import { AuthShell } from "@/features/identity/components/auth-shell";
import { RegisterForm } from "@/features/identity/components/register-form";

export default function RegisterPage() {
  return (
    <AuthShell
      eyebrow="Create your identity"
      title="Start with one account."
      description="Create a shared DIVS identity first. You will choose driver or client registration separately."
    >
      <RegisterForm />
    </AuthShell>
  );
}
