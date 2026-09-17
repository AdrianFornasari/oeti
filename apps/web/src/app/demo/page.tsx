import Link from "next/link";
import { DemoShell, PrototypeNote } from "./demo-shell";
import styles from "./demo.module.css";

const metrics = [
  { value: "37", label: "New signals", detail: "Last 24 hours", icon: "●", color: styles.red },
  { value: "8", label: "Active threats", detail: "Under monitoring", icon: "◈", color: styles.orange },
  { value: "12", label: "Countries / regions", detail: "With recent signals", icon: "◎", color: styles.blue },
  { value: "3", label: "One Health convergence", detail: "Human · Animal · Environment", icon: "△", color: styles.green },
];

const threats = [
  { name: "Hantavirus", region: "MV Hondius adjudicated case", domains: "Human · Wildlife · Genomic · Mobility", level: "Case demo", href: "/demo/threats/hantavirus", pill: styles.pillHigh },
  { name: "Influenza A(H5N1)", region: "Southern Cone", domains: "Animal · Human", level: "Illustrative", href: "/demo", pill: styles.pillHigh },
  { name: "Oropouche", region: "South America", domains: "Human · Environment", level: "Illustrative", href: "/demo", pill: styles.pillMedium },
  { name: "mpox", region: "Central Africa", domains: "Human", level: "Illustrative", href: "/demo", pill: styles.pillMedium },
  { name: "Rift Valley Fever", region: "East Africa", domains: "Animal · Environment", level: "Illustrative", href: "/demo", pill: styles.pillLow },
];

const signals = [
  ["29 Jun", "Hantavirus", "Ushuaia, Argentina", "Laboratory result", "Wildlife", "ANLIS-Malbrán"],
  ["26 May", "Hantavirus", "MV Hondius", "Outbreak update", "Human", "BEN SE19"],
  ["19 May", "Hantavirus", "MV Hondius", "Transmission observation", "Human", "BEN SE18"],
  ["12 May", "Hantavirus", "MV Hondius", "Outbreak update", "Human", "BEN SE17"],
];

export default function SponsorDemoPage() {
  return (
    <DemoShell active="dashboard">
      <div className={styles.content}>
        <PrototypeNote>Executive dashboard prototype — the MV Hondius guided-demo route is grounded in adjudicated OETI corpus data; the global portfolio metrics and non-Hantavirus threats remain illustrative.</PrototypeNote>
        <div className={styles.pageHead}>
          <div>
            <div className={styles.breadcrumb}>Executive Dashboard</div>
            <h1>Global threats. A healthier tomorrow.</h1>
            <p className={styles.subtitle}>Integrating human, animal and environmental intelligence for earlier detection and stronger response.</p>
          </div>
          <div className={styles.actions}><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/threats/hantavirus">Open guided demo →</Link></div>
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
            <h2>Geographic overview</h2>
            <div className={styles.map} aria-label="Conceptual geographic threat map">
              <div className={styles.continent} />
              <span className={`${styles.marker} ${styles.markerHuman}`} style={{ left: "55%", top: "76%" }} />
              <span className={`${styles.marker} ${styles.markerAnimal}`} style={{ left: "51%", top: "58%" }} />
              <span className={`${styles.marker} ${styles.markerEnv}`} style={{ left: "43%", top: "38%" }} />
              <span className={`${styles.marker} ${styles.markerAmber}`} style={{ left: "25%", top: "44%" }} />
              <div className={styles.legend}><div><span className={`${styles.dot} ${styles.dotHuman}`} />Human</div><div><span className={`${styles.dot} ${styles.dotAnimal}`} />Animal</div><div><span className={`${styles.dot} ${styles.dotEnv}`} />Environment</div></div>
            </div>
          </article>

          <article className={styles.card}>
            <h2>Top emerging threats</h2>
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
          <h2>Recent Hantavirus demo signals</h2>
          <table className={styles.table}>
            <thead><tr><th>Date</th><th>Pathogen / Disease</th><th>Location / context</th><th>Signal type</th><th>One Health domain</th><th>Source</th></tr></thead>
            <tbody>{signals.map((signal) => <tr key={`${signal[0]}-${signal[2]}-${signal[3]}`}>{signal.map((cell, index) => <td key={`${cell}-${index}`}>{cell}</td>)}</tr>)}</tbody>
          </table>
        </section>
      </div>
    </DemoShell>
  );
}
