"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "./demo/demo-shell";
import { DemoPreferencesProvider, useDemoPreferences } from "./demo/demo-preferences";
import styles from "./demo/demo.module.css";
import "./demo/demo-responsive.css";
import "./demo/demo-font-scale.css";

function HomeContent() {
  const { isSpanish } = useDemoPreferences();

  return (
    <DemoShell active="dashboard">
      <div className={styles.content} style={{ minWidth: 0, overflowWrap: "anywhere" }}>
        <PrototypeNote>{isSpanish
          ? "Demostración de OETI — combina un caso documental adjudicado con elementos ilustrativos y resultados históricos. Las decisiones de revisión se guardan sólo en este navegador."
          : "OETI demonstration — combines an adjudicated documentary case with illustrative elements and historical results. Review decisions are stored only in this browser."}</PrototypeNote>
        <div className={styles.pageHead}>
          <div>
            <div className={styles.breadcrumb}>{isSpanish ? "Bienvenido a OETI" : "Welcome to OETI"}</div>
            <h1>One Health Emerging Threat Intelligence</h1>
            <p className={styles.subtitle}>{isSpanish
              ? "De la evidencia documental a señales revisables de salud humana, animal y ambiental."
              : "From documentary evidence to reviewable human, animal and environmental health signals."}</p>
          </div>
        </div>
        <section className={styles.card}>
          <h2>{isSpanish ? "Explorá la demostración" : "Explore the demonstration"}</h2>
          <p>{isSpanish
            ? "Recorré el caso MV Hondius para ver sus documentos, señales, evidencia e incertidumbre. El panel general incluye indicadores ilustrativos; la evaluación muestra una corrida histórica v0.4.4."
            : "Explore the MV Hondius case to see its documents, signals, evidence and uncertainty. The overview dashboard includes illustrative indicators; evaluation shows a historical v0.4.4 run."}</p>
          <div className={styles.actions}>
            <Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo">{isSpanish ? "Entrar a la demo →" : "Enter demo →"}</Link>
            <Link className={styles.button} href="/demo/presentation">{isSpanish ? "Guía para presentar" : "Presentation guide"}</Link>
          </div>
        </section>
        <section className={styles.card} style={{ marginTop: 14 }}>
          <h2>{isSpanish ? "Qué vas a encontrar" : "What you will find"}</h2>
          <div className={styles.summaryList}>
            <div className={styles.summaryRow}>
              <div className={styles.summaryKey}>{isSpanish ? "Trazabilidad" : "Traceability"}</div>
              <div>{isSpanish ? "Desde el fragmento fuente hasta la afirmación extraída y la señal." : "From the source excerpt to the extracted claim and signal."}</div>
            </div>
            <div className={styles.summaryRow}>
              <div className={styles.summaryKey}>{isSpanish ? "Revisión humana" : "Human review"}</div>
              <div>{isSpanish ? "Una decisión separada de la propuesta automática, sin modificar producción ni el corpus adjudicado." : "A decision separate from the machine proposal, without modifying production or the adjudicated corpus."}</div>
            </div>
            <div className={styles.summaryRow}>
              <div className={styles.summaryKey}>{isSpanish ? "Evaluación histórica" : "Historical evaluation"}</div>
              <div>{isSpanish ? "Resultados de una corrida definida; no representan el desempeño ni el estado actual del backend." : "Results from a defined run; they do not represent current backend performance or state."}</div>
            </div>
          </div>
        </section>
      </div>
    </DemoShell>
  );
}

export default function HomePage() {
  return <DemoPreferencesProvider><HomeContent /></DemoPreferencesProvider>;
}
