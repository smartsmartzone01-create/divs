import Link from "next/link";
import { AuthShell } from "@/features/identity/components/auth-shell";
import { RegisterForm } from "@/features/identity/components/register-form";

export default function RegisterPage() {
  return (
    <AuthShell
      eyebrow="Create your identity"
      title="Create your DIVS account"
      description="Use your email address, mobile number, or Google account to get started."
      footer={<span>Already have an account? <Link href="/sign-in">Log in</Link></span>}
    >
      <RegisterForm />
    </AuthShell>
  );
}
