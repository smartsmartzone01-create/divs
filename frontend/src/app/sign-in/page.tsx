import Link from "next/link";
import { AuthShell } from "@/features/identity/components/auth-shell";
import { SignInForm } from "@/features/identity/components/sign-in-form";

export default function SignInPage() {
  return (
    <AuthShell
      eyebrow="Welcome back"
      title="Sign in to DIVS."
      description="Use your verified email or phone number and password to access your account."
      footer={<span>New to DIVS? <Link href="/register">Create an account</Link></span>}
    >
      <SignInForm />
    </AuthShell>
  );
}
