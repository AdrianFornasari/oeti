"use client";

import { useEffect, useState } from "react";

export type DemoReviewDecision = "confirm" | "correct" | "reject";

export type DemoReviewRecord = {
  signalId: string;
  decision: DemoReviewDecision;
  status: "analyst_confirmed" | "analyst_corrected" | "analyst_rejected";
  note: string;
  correctedSummary?: string;
  correctedType?: string;
  correctedRole?: string;
};

const STORAGE_KEY = "oeti-demo-review-asm-01";

function readRecord(): DemoReviewRecord | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as DemoReviewRecord;
    if (!parsed || typeof parsed !== "object" || !parsed.signalId || !parsed.decision || !parsed.status) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function useDemoReviewState(signalId: string) {
  const [record, setRecord] = useState<DemoReviewRecord | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const stored = readRecord();
    setRecord(stored?.signalId === signalId ? stored : null);
    setHydrated(true);
  }, [signalId]);

  const saveRecord = (next: DemoReviewRecord) => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setRecord(next);
  };

  const clearRecord = () => {
    window.localStorage.removeItem(STORAGE_KEY);
    setRecord(null);
  };

  return { record, hydrated, saveRecord, clearRecord };
}
