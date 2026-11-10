"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useDIVSPreferences } from "@/components/preferences/preferences-provider";

export type FeedbackTone = "error" | "success" | "info" | "warning";
export type FeedbackInput = {
  message: string;
  tone: FeedbackTone;
  anchorId?: string;
  persistent?: boolean;
};

type FeedbackItem = FeedbackInput & { id: number };
type FeedbackContextValue = {
  showFeedback: (input: FeedbackInput) => number;
  dismissFeedback: (id: number) => void;
};

const FeedbackContext = createContext<FeedbackContextValue | null>(null);
let nextFeedbackId = 1;

function FeedbackCard({ item, onDismiss }: { item: FeedbackItem; onDismiss: () => void }) {
  const labels = {
    en: { error: "Error", success: "Success", info: "Information", warning: "Warning", dismiss: "Dismiss message" },
    sw: { error: "Hitilafu", success: "Imefanikiwa", info: "Taarifa", warning: "Tahadhari", dismiss: "Funga ujumbe" },
  };
  const { language } = useDIVSPreferences();
  const copy = labels[language];
  return (
    <div className={`divs-feedback-card is-${item.tone}`} role={item.tone === "error" ? "alert" : "status"} aria-live={item.tone === "error" ? "assertive" : "polite"}>
      <span className="divs-feedback-indicator" aria-hidden="true" />
      <div className="divs-feedback-copy">
        <strong>{copy[item.tone]}</strong>
        <p>{item.message}</p>
      </div>
      <button type="button" className="divs-feedback-dismiss" onClick={onDismiss} aria-label={copy.dismiss}>×</button>
    </div>
  );
}

export function FeedbackRegion({ anchorId }: { anchorId: string }) {
  const context = useContext(FeedbackContext);
  if (!context) throw new Error("FeedbackRegion must be used inside DIVSFeedbackProvider");
  const { items, dismiss } = useFeedbackItems();
  return (
    <div className="divs-feedback-region" data-feedback-anchor={anchorId}>
      {items.filter((item) => item.anchorId === anchorId).map((item) => (
        <FeedbackCard key={item.id} item={item} onDismiss={() => context.dismissFeedback(item.id)} />
      ))}
    </div>
  );
}

// Internal subscription hook is shared by anchored regions and the global fallback.
const ItemsContext = createContext<{ items: FeedbackItem[]; dismiss: (id: number) => void } | null>(null);

function useFeedbackItems() {
  const value = useContext(ItemsContext);
  if (!value) throw new Error("Feedback items are unavailable outside DIVSFeedbackProvider");
  return value;
}

export function DIVSFeedbackProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const showFeedback = useCallback((input: FeedbackInput) => {
    const id = nextFeedbackId++;
    setItems((current) => [...current, { ...input, id }]);
    return id;
  }, []);
  const dismissFeedback = useCallback((id: number) => {
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  useEffect(() => {
    const timers = items.filter((item) => !item.persistent).map((item) =>
      window.setTimeout(() => dismissFeedback(item.id), item.tone === "success" ? 4000 : 6500),
    );
    return () => timers.forEach(window.clearTimeout);
  }, [items, dismissFeedback]);

  const contextValue = useMemo(() => ({ showFeedback, dismissFeedback }), [showFeedback, dismissFeedback]);
  const itemsValue = useMemo(() => ({ items, dismiss: dismissFeedback }), [items, dismissFeedback]);
  const globalItems = items.filter((item) => !item.anchorId);

  return (
    <FeedbackContext.Provider value={contextValue}>
      <ItemsContext.Provider value={itemsValue}>
        {children}
        <div className="divs-global-feedback" aria-label="DIVS notifications">
          {globalItems.map((item) => (
            <FeedbackCard key={item.id} item={item} onDismiss={() => dismissFeedback(item.id)} />
          ))}
        </div>
      </ItemsContext.Provider>
    </FeedbackContext.Provider>
  );
}

export function useDIVSFeedback() {
  const context = useContext(FeedbackContext);
  if (!context) throw new Error("useDIVSFeedback must be used inside DIVSFeedbackProvider");
  return context;
}
