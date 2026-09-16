import Link from "next/link";
import styles from "./demo.module.css";

const metrics = [
  { value: "37", label: "New signals", detail: "Last 24 hours", icon: "●", color: styles.red },
  { value: "8", label: "Active threats", detail: "Under monitoring", icon: "◈", color: styles.orange },
  { value: "12", label: "Countries / regions", detail: "With recent signals", icon: "◎", color: styles.blue },
  { value: "3", label: "One Health convergence", detail: "Human · Animal · Environment", icon: "△", color: styles.green },
];

const threats = [
  { name: "Hantavirus", region: "Tierra del Fuego, Argentina", domains: "Human · Animal · Environment", level: "High", href: "/demo/threats/hantavirus", pill: styles.pillHigh },
  { name: "Influenza A(H5N1)", region: "Southern Cone", domains: "Animal · Human", level: "High", href: "#", pill: styles.pillHigh },
  { name: "Oropouche", region: "South America", domains: "Human · Environment", level: "Medium", href: "#", pill: styles.pillMedium },
  { name: "mpox", region: "Central Africa", domains: "Human", level: "Medium", href: "#", pill: styles.pillMedium },
  { name: "Rift Valley Fever", region: "East Africa", domains: "Animal · Environment", level: "Low", href: "#", pill: styles.pillLow },
];

const signals = [
  ["14:32", "Hantavirus", "Ushuaia, Argentina", "Laboratory result", "Animal", "Scientific publication"],
  ["12:17", "Influenza A(H5N1)", "Rio Grande, Brazil", "Outbreak", "Animal", "News report"],
  ["09:42", "Oropouche", "Santa Cruz, Bolivia", "Human case", "Human", "Health authority"],
  ["08:11", "mpox", "Kinshasa, DRC", "Human case", "Human", "Health authority"],
];

function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <div className={styles.logo} />
        <div className={styles.brandText}>
          <div className={styles.brandTitle}>OETI</div>
          <span className={styles.brandSub}>One Health Emerging<br />Threat Intelligence</span>
        </div>
      </div>
      <nav className={styles.nav}>
        <Link className={`${styles.navLink} ${styles.active}`} href="/demo"><span className={styles.navIcon}>⌂</span><span className={styles.navText}>Dashboard</span></Link>
        <Link className={styles.navLink} href="/demo/threats/hantavirus"><span className={styles.navIcon}>◈</span><span className={styles.navText}>Threats</span></Link>
        <a className={styles.navLink} href="#signals"><span className={styles.navIcon}>◉</span><span className={styles.navText}>Signals</span></a>
        <a className={styles.navLink} href="#"><span className={styles.navIcon}>▤</span><span className={styles.navText}>Evidence</span></a>
        <a className={styles.navLink} href="#"><span className={styles.navIcon}>▥</span><span className={styles.navText}>Evaluation</span></a>
      </nav>
      <div className={styles.sidebarFooter}>Sponsor demo branch<br />Concept data</div>
    </aside>
  );
}

function Topbar() {
  return (
    <div className={styles.topbar}>
      <div className={styles.search}><input aria-label="Search" placeholder="Search threats, signals, pathogens, locations or keywords…" /></div>
      <div className={styles.topSpacer} />
      <div className={styles.date}>16 September 2026</div>
      <div className={styles.analyst}><div className={styles.avatar}>AR</div>Analyst ▾</div>
    </div>
  );
}

export default function SponsorDemoPage() {
  return (
    <div className={styles.app}>
      <Sidebar />
      <main className={styles.main}>
        <Topbar />
        <div className={styles.content}>
          <div className={styles.prototypeNote}>Concept prototype — data shown on this screen are illustrative and are not current production surveillance results.</div>
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

          <section id="signals" className={`${styles.card} ${styles.tableWrap}`}>
            <h2>Recent signals</h2>
            <table className={styles.table}>
              <thead><tr><th>Time</th><th>Pathogen / Disease</th><th>Location</th><th>Signal type</th><th>One Health domain</th><th>Source</th></tr></thead>
              <tbody>{signals.map((signal) => <tr key={`${signal[0]}-${signal[1]}`}>{signal.map((cell) => <td key={cell}>{cell}</td>)}</tr>)}</tbody>
            </table>
          </section>
        </div>
      </main>
    </div>
  );
}
