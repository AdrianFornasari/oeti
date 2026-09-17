import Link from "next/link";
import type { ReactNode } from "react";
import styles from "./demo.module.css";

type DemoSection = "dashboard" | "threats" | "signals" | "evidence" | "evaluation";

const navItems: Array<{ key: DemoSection; label: string; icon: string; href: string }> = [
  { key: "dashboard", label: "Dashboard", icon: "⌂", href: "/demo" },
  { key: "threats", label: "Threats", icon: "◈", href: "/demo/threats/hantavirus" },
  { key: "signals", label: "Signals", icon: "◉", href: "/demo/signals/asm-01" },
  { key: "evidence", label: "Evidence", icon: "▤", href: "/demo/evidence/asm-01" },
  { key: "evaluation", label: "Evaluation", icon: "▥", href: "/demo/evaluation" },
];

export function DemoShell({ active, children }: { active: DemoSection; children: ReactNode }) {
  return (
    <div className={styles.app}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <div className={styles.logo} />
          <div className={styles.brandText}>
            <div className={styles.brandTitle}>OETI</div>
            <span className={styles.brandSub}>One Health Emerging<br />Threat Intelligence</span>
          </div>
        </div>
        <nav className={styles.nav}>
          {navItems.map((item) => (
            <Link key={item.key} className={`${styles.navLink} ${active === item.key ? styles.active : ""}`} href={item.href}>
              <span className={styles.navIcon}>{item.icon}</span>
              <span className={styles.navText}>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className={styles.sidebarFooter}>Sponsor demo branch<br />Concept data</div>
      </aside>
      <main className={styles.main}>
        <div className={styles.topbar}>
          <div className={styles.search}><input aria-label="Search" placeholder="Search threats, signals, pathogens, locations or keywords…" /></div>
          <div className={styles.topSpacer} />
          <div className={styles.date}>16 September 2026</div>
          <div className={styles.analyst}><div className={styles.avatar}>AR</div>Analyst ▾</div>
        </div>
        {children}
      </main>
    </div>
  );
}

export function PrototypeNote({ children }: { children?: ReactNode }) {
  return <div className={styles.prototypeNote}>{children ?? "Concept prototype — data shown here are illustrative pending backend integration."}</div>;
}
