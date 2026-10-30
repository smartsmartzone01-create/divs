import Link from "next/link";
import { AuthShell } from "@/features/identity/components/auth-shell";
import { SignInForm } from "@/features/identity/components/sign-in-form";

export default function SignInPage() {
  return (
    <AuthShell
      eyebrow="Welcome back"
      title="Log in"
      description="Don't have an account? Create one to get started with DIVS."
      footer={<span>New to DIVS? <Link href="/register">Sign up</Link></span>}
    >
      <SignInForm />
    </AuthShell>
  );
}
