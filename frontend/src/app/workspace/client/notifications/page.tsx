"use client";

import { NotificationsPage } from "@/components/workspace/notifications-page";

export default function ClientNotificationsPage() {
  return <NotificationsPage role="client" backHref="/workspace/client" backLabel={{ en: "Client workspace", sw: "Nafasi ya mteja" }} />;
}
