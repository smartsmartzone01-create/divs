"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { WorkspaceHeader } from "@/components/workspace/workspace-header";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";
import { apiRequest, ApiError } from "@/lib/api/client";

type NotificationItem = {
  id: string;
  title: string;
  message: string;
  created_at: string;
  read_at: string | null;
  is_read?: boolean;
};

type NotificationResponse = {
  unread_count: number;
  results: NotificationItem[];
};

type Props = {
  role: "driver" | "client" | "operations";
  backHref: string;
  backLabel: { en: string; sw: string };
};

export function NotificationsPage({ role, backHref, backLabel }: Props) {
  const { language } = useDIVSPreferences();
  const sw = language === "sw";
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<"all" | "unread">("all");

  async function loadNotifications() {
    setError("");
    try {
      const response = await apiRequest<NotificationResponse>(`notifications/${role}/`);
      setItems(response.results ?? []);
    } catch (caught) {
      const apiError = caught instanceof ApiError ? caught : null;
      setError(
        apiError?.status === 403
          ? (sw ? "Huna ruhusa ya kuona arifa hizi." : "You do not have permission to view these notifications.")
          : (sw ? "Imeshindikana kupakia arifa. Tafadhali jaribu tena." : "We couldn't load your notifications. Please try again."),
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadNotifications();
  }, [role, sw]);

  async function markAsRead(item: NotificationItem) {
    if (item.read_at || busyId) return;
    setBusyId(item.id);
    setError("");
    try {
      const updated = await apiRequest<NotificationItem>(
        `notifications/${role}/${item.id}/read/`,
        { method: "POST" },
      );
      setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, ...updated } : entry));
    } catch {
      setError(sw ? "Arifa haikuweza kuwekwa kuwa imesomwa." : "We couldn't mark this notification as read.");
    } finally {
      setBusyId("");
    }
  }

  const unreadCount = items.filter((item) => !item.read_at && !item.is_read).length;
  const visibleItems = filter === "unread"
    ? items.filter((item) => !item.read_at && !item.is_read)
    : items;

  return (
    <main className="workspace-shell">
      <WorkspaceHeader />
      <div className="workspace-content">
        <Link href={backHref} className="workspace-link text-sm">← {sw ? backLabel.sw : backLabel.en}</Link>
        <header className="mt-6">
          <p className="workspace-eyebrow">{sw ? "TAARIFA ZA AKAUNTI" : "ACCOUNT UPDATES"}</p>
          <h1 className="workspace-title">{sw ? "Arifa" : "Notifications"}</h1>
          <p className="workspace-description">{sw ? "Taarifa na masasisho yanayohusiana na akaunti yako." : "Updates and messages related to your account."}</p>
        </header>

        <section className="mt-6 flex flex-wrap items-center justify-between gap-3">
          <div className="workspace-card flex items-center gap-3 px-4 py-3">
            <strong className="text-2xl">{unreadCount}</strong>
            <span className="text-sm">{sw ? "Hazijasomwa" : "Unread"}</span>
          </div>
          <div className="flex gap-2" role="group" aria-label={sw ? "Chuja arifa" : "Filter notifications"}>
            <button type="button" className={filter === "all" ? "workspace-primary-button" : "workspace-secondary-button"} onClick={() => setFilter("all")}>{sw ? "Zote" : "All"}</button>
            <button type="button" className={filter === "unread" ? "workspace-primary-button" : "workspace-secondary-button"} onClick={() => setFilter("unread")}>{sw ? "Hazijasomwa" : "Unread"}</button>
          </div>
        </section>

        {error ? <p className="workspace-alert mt-5" role="alert">{error}</p> : null}
        {loading ? <p className="workspace-muted mt-8">{sw ? "Inapakia arifa…" : "Loading notifications…"}</p> :
          visibleItems.length === 0 ? (
            <section className="workspace-card mt-6 p-8 text-center">
              <h2 className="font-semibold">{filter === "unread" ? (sw ? "Hakuna arifa ambazo hazijasomwa" : "No unread notifications") : (sw ? "Bado hakuna arifa" : "No notifications yet")}</h2>
              <p className="workspace-muted mt-2 text-sm">{sw ? "Arifa mpya zitaonekana hapa zitakapopatikana." : "New notifications will appear here when they become available."}</p>
            </section>
          ) : (
            <div className="mt-6 grid gap-3">
              {visibleItems.map((item) => {
                const isRead = Boolean(item.read_at || item.is_read);
                return (
                  <article key={item.id} className={`workspace-card p-4 ${isRead ? "" : "border-l-4 border-l-[#2f75b5]"}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="font-semibold">{item.title}</h2>
                          {!isRead ? <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-900">{sw ? "Mpya" : "New"}</span> : null}
                        </div>
                        <p className="mt-2 whitespace-pre-wrap text-sm">{item.message}</p>
                        <time className="workspace-muted mt-3 block text-xs" dateTime={item.created_at}>{new Date(item.created_at).toLocaleString(sw ? "sw-TZ" : "en-GB")}</time>
                      </div>
                      {!isRead ? <button type="button" className="workspace-secondary-button shrink-0" disabled={busyId === item.id} onClick={() => void markAsRead(item)}>{busyId === item.id ? (sw ? "Inahifadhi…" : "Saving…") : (sw ? "Weka kuwa imesomwa" : "Mark as read")}</button> : <span className="workspace-muted shrink-0 text-xs">{sw ? "Imesomwa" : "Read"}</span>}
                    </div>
                  </article>
                );
              })}
            </div>
          )
        }
      </div>
    </main>
  );
}
