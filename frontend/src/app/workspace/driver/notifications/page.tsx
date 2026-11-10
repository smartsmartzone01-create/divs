"use client";

import { NotificationsPage } from "@/components/workspace/notifications-page";

export default function DriverNotificationsPage() {
  return <NotificationsPage role="driver" backHref="/workspace/driver" backLabel={{ en: "Driver workspace", sw: "Nafasi ya dereva" }} />;
}
