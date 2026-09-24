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
    { value: "37", label: "Señales nuevas", detail: "Últimas 24 horas", icon: "●", color: styles.red },
    { value: "8", label: "Amenazas activas", detail: "Bajo monitoreo", icon: "◈", color: styles.orange },
    { value: "12", label: "Países / regiones", detail: "Con señales recientes", icon: "◎", color: styles.blue },
    { value: "3", label: "Convergencia One Health", detail: "Humana · Animal · Ambiente", icon: "△", color: styles.green },
  ] : [
    { value: "37", label: "New signals", detail: "Last 24 hours", icon: "●", color: styles.red },
    { value: "8", label: "Active threats", detail: "Under monitoring", icon: "◈", color: styles.orange },
    { value: "12", label: "Countries / regions", detail: "With recent signals", icon: "◎", color: styles.blue },
    { value: "3", label: "One Health convergence", detail: "Human · Animal · Environment", icon: "△", color: styles.green },
  ];

  const threats = isSpanish ? [
    { name: "Hantavirus", region: "Caso adjudicado MV Hondius", domains: "Humana · Fauna silvestre · Genómica · Movilidad", level: "Caso demo", href: "/demo/threats/hantavirus", pill: styles.pillHigh },
    { name: "Influenza A(H5N1)", region: "Cono Sur", domains: "Animal · Humana", level: "Ilustrativo", href: "/demo", pill: styles.pillHigh },
    { name: "Oropouche", region: "América del Sur", domains: "Humana · Ambiente", level: "Ilustrativo", href: "/demo", pill: styles.pillMedium },
    { name: "mpox", region: "África Central", domains: "Humana", level: "Ilustrativo", href: "/demo", pill: styles.pillMedium },
    { name: "Fiebre del Valle del Rift", region: "África Oriental", domains: "Animal · Ambiente", level: "Ilustrativo", href: "/demo", pill: styles.pillLow },
  ] : [
    { name: "Hantavirus", region: "MV Hondius adjudicated case", domains: "Human · Wildlife · Genomic · Mobility", level: "Case demo", href: "/demo/threats/hantavirus", pill: styles.pillHigh },
    { name: "Influenza A(H5N1)", region: "Southern Cone", domains: "Animal · Human", level: "Illustrative", href: "/demo", pill: styles.pillHigh },
    { name: "Oropouche", region: "South America", domains: "Human · Environment", level: "Illustrative", href: "/demo", pill: styles.pillMedium },
    { name: "mpox", region: "Central Africa", domains: "Human", level: "Illustrative", href: "/demo", pill: styles.pillMedium },
    { name: "Rift Valley Fever", region: "East Africa", domains: "Animal · Environment", level: "Illustrative", href: "/demo", pill: styles.pillLow },
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
          ? "Prototipo de panel ejecutivo — la ruta guiada del caso MV Hondius se basa en datos adjudicados del corpus OETI; las métricas globales y las amenazas no relacionadas con hantavirus siguen siendo ilustrativas. El estado de revisión de ASM-01 proviene únicamente de localStorage de esta demo."
          : "Executive dashboard prototype — the MV Hondius guided-demo route is grounded in adjudicated OETI corpus data; global portfolio metrics and non-Hantavirus threats remain illustrative. ASM-01 review state comes only from this demo browser localStorage."}
        </PrototypeNote>

        <div className={styles.pageHead}>
          <div>
            <div className={styles.breadcrumb}>{isSpanish ? "Panel ejecutivo" : "Executive Dashboard"}</div>
            <h1>{isSpanish ? "Amenazas globales. Un mañana más saludable." : "Global threats. A healthier tomorrow."}</h1>
            <p className={styles.subtitle}>{isSpanish
              ? "Integrando inteligencia de salud humana, animal y ambiental para una detección más temprana y una respuesta más sólida."
              : "Integrating human, animal and environmental intelligence for earlier detection and stronger response."}</p>
          </div>
          <div className={styles.actions}><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/threats/hantavirus">{isSpanish ? "Abrir demo guiada →" : "Open guided demo →"}</Link></div>
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
            <h2>{isSpanish ? "Panorama geográfico" : "Geographic overview"}</h2>
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
            <h2>{isSpanish ? "Principales amenazas emergentes" : "Top emerging threats"}</h2>
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
              <h2>{isSpanish ? "Adjudicación humana visible downstream" : "Human adjudication visible downstream"}</h2>
              <p className={`${styles.small} ${styles.muted}`} style={{ marginBottom: 0 }}>{isSpanish ? "ASM-01 conserva la propuesta automática y agrega una capa separada de revisión humana." : "ASM-01 preserves the machine proposal and adds a separate human-review layer."}</p>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <span className={`${styles.pill} ${record ? styles.pillReviewed : styles.pillActive}`}>{reviewLabel}</span>
              <Link className={styles.button} href="/demo/signals/asm-01">{isSpanish ? "Abrir ASM-01" : "Open ASM-01"}</Link>
            </div>
          </div>
        </section>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>{isSpanish ? "Señales recientes de la demo de hantavirus" : "Recent Hantavirus demo signals"}</h2>
          <table className={styles.table}>
            <thead><tr><th>{isSpanish ? "Fecha" : "Date"}</th><th>{isSpanish ? "Patógeno / Enfermedad" : "Pathogen / Disease"}</th><th>{isSpanish ? "Ubicación / contexto" : "Location / context"}</th><th>{isSpanish ? "Tipo de señal" : "Signal type"}</th><th>{isSpanish ? "Dominio One Health" : "One Health domain"}</th><th>{isSpanish ? "Fuente" : "Source"}</th><th>{isSpanish ? "Revisión" : "Review"}</th></tr></thead>
            <tbody>{signals.map((signal, rowIndex) => <tr key={`${signal[0]}-${signal[2]}-${signal[3]}`}>{signal.map((cell, index) => <td key={`${cell}-${index}`}>{cell}</td>)}<td>{rowIndex === 0 ? <span className={`${styles.pill} ${record ? styles.pillReviewed : styles.pillActive}`}>{reviewLabel}</span> : "—"}</td></tr>)}</tbody>
          </table>
        </section>
      </div>
    </DemoShell>
  );
}
