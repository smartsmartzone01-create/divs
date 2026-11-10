"use client";

import { NotificationsPage } from "@/components/workspace/notifications-page";

export default function AdminNotificationsPage() {
  return <NotificationsPage role="operations" backHref="/workspace/admin" backLabel={{ en: "Operations workspace", sw: "Nafasi ya uendeshaji" }} />;
}
