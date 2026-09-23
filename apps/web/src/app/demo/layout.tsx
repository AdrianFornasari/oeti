import type { ReactNode } from "react";
import { DemoPreferencesProvider } from "./demo-preferences";

export default function DemoLayout({ children }: { children: ReactNode }) {
  return <DemoPreferencesProvider>{children}</DemoPreferencesProvider>;
}
