/**
 * Traceability store — the demo centerpiece.
 *
 * Any SourcePill (report number, extraction chip, chat citation, anomaly)
 * dispatches a focus with { document_id, page, bbox, confidence }. A single
 * SourcePanelHost renders the panel. Reverse direction: hovering the bbox in
 * the page viewer re-highlights the calling pill via `focusOrigin`.
 */
import { create } from "zustand";
import type { SourceRef } from "../types";

export interface TraceFocus {
  ref: SourceRef;
  /** where the click came from so we can cross-highlight back */
  origin: "report" | "field" | "chat" | "anomaly" | "export";
  open: boolean;
}

interface TraceState {
  focus: TraceFocus | null;
  /** used by pages to know WHICH pill is currently cross-highlighted */
  activeRefKey: string | null;
  dismiss: () => void;
  focusRef: (ref: SourceRef, origin: TraceFocus["origin"]) => void;
  hoverRef: (key: string | null) => void;
}

/** Stable key for cross-highlight matching on both sides. */
export function refKey(ref: Pick<SourceRef, "document_id" | "page" | "value">): string {
  return `${ref.document_id}:${ref.page}:${String(ref.value)}`;
}

export const useTraceStore = create<TraceState>((set) => ({
  focus: null,
  activeRefKey: null,
  dismiss: () => set((s) => (s.focus ? { ...s, focus: { ...s.focus, open: false } } : s)),
  focusRef: (ref, origin) => {
    const key = refKey(ref);
    set({ focus: { ref, origin, open: true }, activeRefKey: key });
  },
  hoverRef: (key) => set({ activeRefKey: key }),
}));