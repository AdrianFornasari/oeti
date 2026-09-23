"use client";

import Link from "next/link";
import { useMemo, type ReactNode } from "react";
import { useDemoPreferences } from "./demo-preferences";
import styles from "./demo.module.css";

type DemoSection = "dashboard" | "threats" | "signals" | "evidence" | "evaluation";

const navItems: Array<{ key: DemoSection; en: string; es: string; icon: string; href: string }> = [
  { key: "dashboard", en: "Dashboard", es: "Panel", icon: "⌂", href: "/demo" },
  { key: "threats", en: "Threats", es: "Amenazas", icon: "◈", href: "/demo/threats/hantavirus" },
  { key: "signals", en: "Signals", es: "Señales", icon: "◉", href: "/demo/signals/asm-01" },
  { key: "evidence", en: "Evidence", es: "Evidencia", icon: "▤", href: "/demo/evidence/asm-01" },
  { key: "evaluation", en: "Evaluation", es: "Evaluación", icon: "▥", href: "/demo/evaluation" },
];

export function DemoShell({ active, children }: { active: DemoSection; children: ReactNode }) {
  const { language, theme, setLanguage, setTheme, isSpanish } = useDemoPreferences();

  const formattedDate = useMemo(
    () => new Intl.DateTimeFormat(isSpanish ? "es-AR" : "en-GB", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    }).format(new Date()),
    [isSpanish],
  );

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
              <span className={styles.navText}>{isSpanish ? item.es : item.en}</span>
            </Link>
          ))}
        </nav>
        <div className={styles.sidebarFooter}>
          {isSpanish ? <>Rama demo sponsor<br />Datos conceptuales</> : <>Sponsor demo branch<br />Concept data</>}
        </div>
      </aside>

      <main className={styles.main}>
        <div className={styles.topbar}>
          <div className={styles.search}>
            <input
              aria-label={isSpanish ? "Buscar" : "Search"}
              placeholder={isSpanish ? "Buscar amenazas, señales, patógenos, ubicaciones o palabras clave…" : "Search threats, signals, pathogens, locations or keywords…"}
            />
          </div>
          <div className={styles.topSpacer} />

          <div className={styles.preferenceControls}>
            <div className={styles.segmented} aria-label={isSpanish ? "Idioma" : "Language"}>
              <button className={language === "en" ? styles.segmentedActive : ""} onClick={() => setLanguage("en")} aria-pressed={language === "en"}>EN</button>
              <button className={language === "es" ? styles.segmentedActive : ""} onClick={() => setLanguage("es")} aria-pressed={language === "es"}>ES</button>
            </div>
            <button
              className={styles.themeToggle}
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              aria-label={isSpanish ? (theme === "light" ? "Activar modo oscuro" : "Activar modo claro") : (theme === "light" ? "Enable dark mode" : "Enable light mode")}
              title={isSpanish ? (theme === "light" ? "Modo oscuro" : "Modo claro") : (theme === "light" ? "Dark mode" : "Light mode")}
            >
              <span aria-hidden="true">{theme === "light" ? "☾" : "☀"}</span>
              <span className={styles.themeLabel}>{isSpanish ? (theme === "light" ? "Oscuro" : "Claro") : (theme === "light" ? "Dark" : "Light")}</span>
            </button>
          </div>

          <div className={styles.date}>{formattedDate}</div>
          <div className={styles.analyst}><div className={styles.avatar}>AR</div>{isSpanish ? "Analista" : "Analyst"} ▾</div>
        </div>
        {children}
      </main>
    </div>
  );
}

export function PrototypeNote({ children }: { children?: ReactNode }) {
  const { isSpanish } = useDemoPreferences();
  return (
    <div className={styles.prototypeNote}>
      {children ?? (isSpanish
        ? "Prototipo conceptual — los datos mostrados aquí son ilustrativos hasta la integración con backend."
        : "Concept prototype — data shown here are illustrative pending backend integration.")}
    </div>
  );
}
