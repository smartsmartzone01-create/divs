import type { Metadata, Viewport } from "next";
import "./globals.css";
import "./landing-reference.css";
import "./workspace.css";
import { DIVSPreferencesProvider } from "@/components/preferences/preferences-provider";

export const metadata: Metadata = {
  title: {
    default: "DIVS | Driver Identification and Verification System",
    template: "%s | DIVS",
  },
  description:
    "Find and verify professional drivers through the Driver Identification and Verification System.",
};

export const viewport: Viewport = {
  themeColor: "#10233f",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body><DIVSPreferencesProvider>{children}</DIVSPreferencesProvider></body>
    </html>
  );
}
