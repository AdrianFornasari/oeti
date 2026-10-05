import type { ReactNode } from "react";
import { DemoPreferencesProvider } from "./demo-preferences";
import "./demo-responsive.css";
import "./demo-font-scale.css";

export default function DemoLayout({ children }: { children: ReactNode }) {
  return <DemoPreferencesProvider>{children}</DemoPreferencesProvider>;
}
