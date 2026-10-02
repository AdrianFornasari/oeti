"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "./demo-shell";
import { useDemoPreferences } from "./demo-preferences";
import { useDemoReviewState } from "./demo-review-state";
import { ushuaiaRodentSignal } from "./mv-hondius-data";
import styles from "./demo.module.css";

export default function SponsorDemoPage() {
  const { isSpanish } = useDemoPreferences();
  const { record } = useDemoReviewState(ushuaiaRodentSignal.id);

  const reviewLabel = !record
    ? (isSpanish ? "Pendiente" : "Pending")
    : record.decision === "confirm"
      ? (isSpanish ? "Confirmada" : "Confirmed")
      : record.decision === "correct"
        ? (isSpanish ? "Corregida" : "Corrected")
        : (isSpanish ? "Rechazada" : "Rejected");

  const metrics = isSpanish ? [
    { value: "37", label: "Señales nuevas", detail: "Ejemplo visual · últimas 24 horas", icon: "●", color: styles.red },
    { value: "8", label: "Amenazas activas", detail: "Ejemplo visual · bajo monitoreo", icon: "◈", color: styles.orange },
    { value: "12", label: "Países / regiones", detail: "Ejemplo visual · señales recientes", icon: "◎", color: styles.blue },
    { value: "3", label: "Convergencia One Health", detail: "Ejemplo visual · humana · animal · ambiente", icon: "△", color: styles.green },
  ] : [
    { value: "37", label: "New signals", detail: "Visual example · last 24 hours", icon: "●", color: styles.red },
    { value: "8", label: "Active threats", detail: "Visual example · under monitoring", icon: "◈", color: styles.orange },
    { value: "12", label: "Countries / regions", detail: "Visual example · recent signals", icon: "◎", color: styles.blue },
    { value: "3", label: "One Health convergence", detail: "Visual example · human · animal · environment", icon: "△", color: styles.green },
  ];

  const threats = isSpanish ? [
    { name: "Hantavirus", region: "Caso real adjudicado MV Hondius", domains: "Humana · Fauna silvestre · Genómica · Movilidad", level: "Caso real", href: "/demo/threats/hantavirus", pill: styles.pillReviewed },
    { name: "Influenza A(H5N1)", region: "Cono Sur", domains: "Animal · Humana", level: "Ejemplo visual", href: "/demo", pill: "" },
    { name: "Oropouche", region: "América del Sur", domains: "Humana · Ambiente", level: "Ejemplo visual", href: "/demo", pill: "" },
    { name: "mpox", region: "África Central", domains: "Humana", level: "Ejemplo visual", href: "/demo", pill: "" },
    { name: "Fiebre del Valle del Rift", region: "África Oriental", domains: "Animal · Ambiente", level: "Ejemplo visual", href: "/demo", pill: "" },
  ] : [
    { name: "Hantavirus", region: "Real adjudicated MV Hondius case", domains: "Human · Wildlife · Genomic · Mobility", level: "Real case", href: "/demo/threats/hantavirus", pill: styles.pillReviewed },
    { name: "Influenza A(H5N1)", region: "Southern Cone", domains: "Animal · Human", level: "Visual example", href: "/demo", pill: "" },
    { name: "Oropouche", region: "South America", domains: "Human · Environment", level: "Visual example", href: "/demo", pill: "" },
    { name: "mpox", region: "Central Africa", domains: "Human", level: "Visual example", href: "/demo", pill: "" },
    { name: "Rift Valley Fever", region: "East Africa", domains: "Animal · Environment", level: "Visual example", href: "/demo", pill: "" },
  ];

  const signals = isSpanish ? [
    ["29 jun", "Hantavirus", "Ushuaia, Argentina", "Resultado de laboratorio", "Fauna silvestre", "ANLIS-Malbrán"],
    ["26 may", "Hantavirus", "MV Hondius", "Actualización del brote", "Humana", "BEN SE19"],
    ["19 may", "Hantavirus", "MV Hondius", "Observación de transmisión", "Humana", "BEN SE18"],
    ["12 may", "Hantavirus", "MV Hondius", "Actualización del brote", "Humana", "BEN SE17"],
  ] : [
    ["29 Jun", "Hantavirus", "Ushuaia, Argentina", "Laboratory result", "Wildlife", "ANLIS-Malbrán"],
    ["26 May", "Hantavirus", "MV Hondius", "Outbreak update", "Human", "BEN SE19"],
    ["19 May", "Hantavirus", "MV Hondius", "Transmission observation", "Human", "BEN SE18"],
    ["12 May", "Hantavirus", "MV Hondius", "Outbreak update", "Human", "BEN SE17"],
  ];

  return (
    <DemoShell active="dashboard">
      <div className={styles.content}>
        <PrototypeNote>{isSpanish
          ? "Demo para sponsor — el caso MV Hondius y sus señales provienen del corpus adjudicado de OETI. Los indicadores globales, el mapa general y las amenazas distintas de hantavirus son ejemplos visuales de cómo podría verse una operación a escala."
          : "Sponsor demo — the MV Hondius case and its signals come from the adjudicated OETI corpus. Global indicators, the overview map and non-Hantavirus threats are visual examples of how scaled operations could look."}
        </PrototypeNote>

        <div className={styles.pageHead}>
          <div>
            <div className={styles.breadcrumb}>{isSpanish ? "Panel ejecutivo" : "Executive Dashboard"}</div>
            <h1>{isSpanish ? "Amenazas globales. Un mañana más saludable." : "Global threats. A healthier tomorrow."}</h1>
            <p className={styles.subtitle}>{isSpanish
              ? "Integrando inteligencia de salud humana, animal y ambiental para una detección más temprana y una respuesta más sólida."
              : "Integrating human, animal and environmental intelligence for earlier detection and stronger response."}</p>
          </div>
          <div className={styles.actions}><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/threats/hantavirus">{isSpanish ? "Abrir caso real MV Hondius →" : "Open real MV Hondius case →"}</Link></div>
        </div>

        <div className={styles.pageHead} style={{ marginBottom: 8 }}>
          <div><h2 style={{ margin: 0 }}>{isSpanish ? "Vista conceptual de operación" : "Conceptual operations view"}</h2><p className={`${styles.small} ${styles.muted}`} style={{ marginBottom: 0 }}>{isSpanish ? "Indicadores ilustrativos para mostrar la escala futura de la plataforma." : "Illustrative indicators showing the platform's future operating scale."}</p></div>
          <span className={styles.pill}>{isSpanish ? "DATOS ILUSTRATIVOS" : "ILLUSTRATIVE DATA"}</span>
        </div>

        <section className={styles.grid4}>
          {metrics.map((metric) => (
            <article className={`${styles.card} ${styles.metric}`} key={metric.label}>
              <div className={`${styles.metricIcon} ${metric.color}`}>{metric.icon}</div>
              <div><span className={styles.metricValue}>{metric.value}</span><div className={styles.metricLabel}>{metric.label}</div><small className={styles.muted}>{metric.detail}</small></div>
            </article>
          ))}
        </section>

        <section className={styles.dashboardMain}>
          <article className={styles.card}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center" }}><h2>{isSpanish ? "Panorama geográfico" : "Geographic overview"}</h2><span className={styles.pill}>{isSpanish ? "Ilustrativo" : "Illustrative"}</span></div>
            <div className={styles.map} aria-label={isSpanish ? "Mapa conceptual de amenazas" : "Conceptual geographic threat map"}>
              <div className={styles.continent} />
              <span className={`${styles.marker} ${styles.markerHuman}`} style={{ left: "55%", top: "76%" }} />
              <span className={`${styles.marker} ${styles.markerAnimal}`} style={{ left: "51%", top: "58%" }} />
              <span className={`${styles.marker} ${styles.markerEnv}`} style={{ left: "43%", top: "38%" }} />
              <span className={`${styles.marker} ${styles.markerAmber}`} style={{ left: "25%", top: "44%" }} />
              <div className={styles.legend}><div><span className={`${styles.dot} ${styles.dotHuman}`} />{isSpanish ? "Humana" : "Human"}</div><div><span className={`${styles.dot} ${styles.dotAnimal}`} />{isSpanish ? "Animal" : "Animal"}</div><div><span className={`${styles.dot} ${styles.dotEnv}`} />{isSpanish ? "Ambiente" : "Environment"}</div></div>
            </div>
          </article>

          <article className={styles.card}>
            <h2>{isSpanish ? "Amenazas emergentes" : "Emerging threats"}</h2>
            <div className={styles.threatList}>
              {threats.map((threat) => (
                <Link key={threat.name} className={styles.threatItem} href={threat.href}>
                  <div><strong>{threat.name}</strong><div className={`${styles.small} ${styles.muted}`}>{threat.region}</div><div className={`${styles.small} ${styles.muted}`}>{threat.domains}</div></div>
                  <span className={`${styles.pill} ${threat.pill}`}>{threat.level}</span>
                </Link>
              ))}
            </div>
          </article>
        </section>

        <section className={styles.card} style={{ marginTop: 14 }}>
          <div className={styles.pageHead} style={{ marginBottom: 0 }}>
            <div>
              <h2>{isSpanish ? "Revisión humana de la señal" : "Human signal review"}</h2>
              <p className={`${styles.small} ${styles.muted}`} style={{ marginBottom: 0 }}>{isSpanish ? "La señal ASM-01 conserva el resultado automático y, por separado, la decisión del analista." : "ASM-01 preserves the machine result and, separately, the analyst decision."}</p>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <span className={`${styles.pill} ${record ? styles.pillReviewed : styles.pillActive}`}>{reviewLabel}</span>
              <Link className={styles.button} href="/demo/signals/asm-01">{isSpanish ? "Abrir ASM-01" : "Open ASM-01"}</Link>
            </div>
          </div>
        </section>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "center", flexWrap: "wrap" }}><h2>{isSpanish ? "Señales reales del caso MV Hondius" : "Real MV Hondius case signals"}</h2><span className={`${styles.pill} ${styles.pillReviewed}`}>{isSpanish ? "CORPUS ADJUDICADO" : "ADJUDICATED CORPUS"}</span></div>
          <table className={styles.table}>
            <thead><tr><th>{isSpanish ? "Fecha" : "Date"}</th><th>{isSpanish ? "Patógeno / Enfermedad" : "Pathogen / Disease"}</th><th>{isSpanish ? "Ubicación / contexto" : "Location / context"}</th><th>{isSpanish ? "Tipo de señal" : "Signal type"}</th><th>{isSpanish ? "Dominio One Health" : "One Health domain"}</th><th>{isSpanish ? "Fuente" : "Source"}</th><th>{isSpanish ? "Revisión" : "Review"}</th></tr></thead>
            <tbody>{signals.map((signal, rowIndex) => <tr key={`${signal[0]}-${signal[2]}-${signal[3]}`}>{signal.map((cell, index) => <td key={`${cell}-${index}`}>{cell}</td>)}<td>{rowIndex === 0 ? <span className={`${styles.pill} ${record ? styles.pillReviewed : styles.pillActive}`}>{reviewLabel}</span> : "—"}</td></tr>)}</tbody>
          </table>
        </section>
      </div>
    </DemoShell>
  );
}
