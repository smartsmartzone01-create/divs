import Link from "next/link";
import { AuthShell } from "@/features/identity/components/auth-shell";
import { SignInForm } from "@/features/identity/components/sign-in-form";

export default function SignInPage() {
  return (
    <AuthShell
      eyebrow="Welcome back"
      title="Log in"
      description="Access your DIVS account using your verified email, mobile number, or Google."
      footer={<span>New to DIVS? <Link href="/register">Sign up</Link></span>}
    >
      <SignInForm />
    </AuthShell>
  );
}
