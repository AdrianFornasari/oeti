"use client";

import Link from "next/link";
import { useMemo, type ReactNode } from "react";
import { DEMO_FONT_SCALES, useDemoPreferences } from "./demo-preferences";
import styles from "./demo.module.css";
import mobileStyles from "./demo-mobile.module.css";

type DemoSection = "dashboard" | "threats" | "signals" | "evidence" | "evaluation";

const navItems: Array<{ key: DemoSection; en: string; es: string; icon: string; href: string }> = [
  { key: "dashboard", en: "Dashboard", es: "Panel", icon: "⌂", href: "/demo" },
  { key: "threats", en: "Threats", es: "Amenazas", icon: "◈", href: "/demo/threats/hantavirus" },
  { key: "signals", en: "Signals", es: "Señales", icon: "◉", href: "/demo/signals/asm-01" },
  { key: "evidence", en: "Evidence", es: "Evidencia", icon: "▤", href: "/demo/evidence/asm-01" },
  { key: "evaluation", en: "Evaluation", es: "Evaluación", icon: "▥", href: "/demo/evaluation" },
];

export function DemoShell({ active, children }: { active: DemoSection; children: ReactNode }) {
  const { language, theme, fontScale, setLanguage, setTheme, setFontScale, isSpanish } = useDemoPreferences();

  const formattedDate = useMemo(
    () => new Intl.DateTimeFormat(isSpanish ? "es-AR" : "en-GB", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    }).format(new Date()),
    [isSpanish],
  );

  const fontScaleIndex = DEMO_FONT_SCALES.indexOf(fontScale);
  const decreaseFont = () => {
    if (fontScaleIndex <= 0) return;
    setFontScale(DEMO_FONT_SCALES[fontScaleIndex - 1]);
  };
  const increaseFont = () => {
    if (fontScaleIndex < 0 || fontScaleIndex >= DEMO_FONT_SCALES.length - 1) return;
    setFontScale(DEMO_FONT_SCALES[fontScaleIndex + 1]);
  };

  return (
    <div className={styles.app} data-theme={theme} data-demo-shell>
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
          <Link href="/demo/presentation" style={{ display: "inline-block", marginBottom: 10, fontWeight: 700 }}>
            {isSpanish ? "▷ Modo presentación" : "▷ Presentation mode"}
          </Link>
          <br />
          {isSpanish ? <>Rama demo sponsor<br />Datos conceptuales</> : <>Sponsor demo branch<br />Concept data</>}
        </div>
      </aside>

      <main className={styles.main}>
        <div className={`${styles.topbar} ${mobileStyles.topbar}`} data-demo-topbar>
          <div className={`${styles.search} ${mobileStyles.search}`} data-demo-search title={isSpanish ? "Búsqueda ilustrativa en esta demo" : "Illustrative search in this demo"}>
            <input
              aria-label={isSpanish ? "Búsqueda ilustrativa" : "Illustrative search"}
              placeholder={isSpanish ? "Búsqueda ilustrativa — no activa en esta demo" : "Illustrative search — not active in this demo"}
              disabled
            />
          </div>
          <div className={`${styles.topSpacer} ${mobileStyles.spacer}`} />

          <div className={`${styles.preferenceControls} ${mobileStyles.preferences}`} data-demo-preferences>
            <div className={styles.segmented} data-demo-font-scale aria-label={isSpanish ? "Tamaño de fuente" : "Font size"}>
              <button type="button" onClick={decreaseFont} disabled={fontScaleIndex <= 0} aria-label={isSpanish ? "Disminuir tamaño de fuente" : "Decrease font size"}>A−</button>
              <button type="button" onClick={increaseFont} disabled={fontScaleIndex >= DEMO_FONT_SCALES.length - 1} aria-label={isSpanish ? "Aumentar tamaño de fuente" : "Increase font size"}>A+</button>
            </div>
            <div className={`${styles.segmented} ${mobileStyles.language}`} aria-label={isSpanish ? "Idioma" : "Language"} data-demo-language>
              <button type="button" className={language === "en" ? styles.segmentedActive : ""} onClick={() => setLanguage("en")} aria-pressed={language === "en"}>EN</button>
              <button type="button" className={language === "es" ? styles.segmentedActive : ""} onClick={() => setLanguage("es")} aria-pressed={language === "es"}>ES</button>
            </div>
            <button
              type="button"
              className={`${styles.themeToggle} ${mobileStyles.theme}`}
              data-demo-theme-toggle
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              aria-label={isSpanish ? (theme === "light" ? "Activar modo oscuro" : "Activar modo claro") : (theme === "light" ? "Enable dark mode" : "Enable light mode")}
              title={isSpanish ? (theme === "light" ? "Modo oscuro" : "Modo claro") : (theme === "light" ? "Dark mode" : "Light mode")}
            >
              <span aria-hidden="true">{theme === "light" ? "☾" : "☀"}</span>
              <span className={`${styles.themeLabel} ${mobileStyles.themeLabel}`}>{isSpanish ? (theme === "light" ? "Oscuro" : "Claro") : (theme === "light" ? "Dark" : "Light")}</span>
            </button>
          </div>

          <div className={`${styles.date} ${mobileStyles.date}`}>{formattedDate}</div>
          <div className={`${styles.analyst} ${mobileStyles.analyst}`} title={isSpanish ? "Identidad ilustrativa de la demo" : "Illustrative demo identity"}><div className={styles.avatar}>AR</div>{isSpanish ? "Analista demo" : "Demo analyst"}</div>
        </div>
        <div data-demo-scalable-content style={{ fontSize: `${fontScale}em` }}>
          {children}
        </div>
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
