"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "./demo-shell";
import { useDemoPreferences } from "./demo-preferences";
import styles from "./demo.module.css";

export default function SponsorDemoPage() {
  const { isSpanish } = useDemoPreferences();

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
          ? "Prototipo de panel ejecutivo — la ruta guiada del caso MV Hondius se basa en datos adjudicados del corpus OETI; las métricas globales y las amenazas no relacionadas con hantavirus siguen siendo ilustrativas."
          : "Executive dashboard prototype — the MV Hondius guided-demo route is grounded in adjudicated OETI corpus data; the global portfolio metrics and non-Hantavirus threats remain illustrative."}
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

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>{isSpanish ? "Señales recientes de la demo de hantavirus" : "Recent Hantavirus demo signals"}</h2>
          <table className={styles.table}>
            <thead><tr><th>{isSpanish ? "Fecha" : "Date"}</th><th>{isSpanish ? "Patógeno / Enfermedad" : "Pathogen / Disease"}</th><th>{isSpanish ? "Ubicación / contexto" : "Location / context"}</th><th>{isSpanish ? "Tipo de señal" : "Signal type"}</th><th>{isSpanish ? "Dominio One Health" : "One Health domain"}</th><th>{isSpanish ? "Fuente" : "Source"}</th></tr></thead>
            <tbody>{signals.map((signal) => <tr key={`${signal[0]}-${signal[2]}-${signal[3]}`}>{signal.map((cell, index) => <td key={`${cell}-${index}`}>{cell}</td>)}</tr>)}</tbody>
          </table>
        </section>
      </div>
    </DemoShell>
  );
}
