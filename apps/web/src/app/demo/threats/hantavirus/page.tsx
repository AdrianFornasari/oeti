"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import styles from "../../demo.module.css";

const signals = [
  { date: "04 May 2026", name: "Human case", text: "Confirmed human case of hantavirus in a crew member.", domain: "human", color: styles.markerHuman, location: "Ushuaia" },
  { date: "06 May 2026", name: "Investigation", text: "Rodent investigation initiated in Ushuaia.", domain: "animal", color: styles.markerAnimal, location: "Ushuaia" },
  { date: "14 May 2026", name: "Laboratory result", text: "5 Abrothrix rodents seropositive for hantavirus.", domain: "animal", color: styles.markerAnimal, location: "Ushuaia" },
  { date: "22 May 2026", name: "Environmental sampling", text: "Soil samples collected in peri-urban areas.", domain: "environment", color: styles.markerEnv, location: "Ushuaia" },
  { date: "03 Jun 2026", name: "Additional animal case", text: "More seropositive rodents detected.", domain: "animal", color: styles.markerAnimal, location: "Río Grande" },
  { date: "18 Jul 2026", name: "Environmental finding", text: "Hantavirus RNA detected in soil.", domain: "environment", color: styles.markerEnv, location: "Río Grande" },
];

export default function HantavirusThreatPage() {
  const [domain, setDomain] = useState("all");
  const [selected, setSelected] = useState(2);
  const filtered = useMemo(() => signals.filter((signal) => domain === "all" || signal.domain === domain), [domain]);
  const selectedSignal = signals[selected] ?? signals[0];

  return (
    <div className={styles.app}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}><div className={styles.logo} /><div className={styles.brandText}><div className={styles.brandTitle}>OETI</div><span className={styles.brandSub}>One Health Emerging<br />Threat Intelligence</span></div></div>
        <nav className={styles.nav}>
          <Link className={styles.navLink} href="/demo"><span className={styles.navIcon}>⌂</span><span className={styles.navText}>Dashboard</span></Link>
          <Link className={`${styles.navLink} ${styles.active}`} href="/demo/threats/hantavirus"><span className={styles.navIcon}>◈</span><span className={styles.navText}>Threats</span></Link>
          <a className={styles.navLink} href="#"><span className={styles.navIcon}>◉</span><span className={styles.navText}>Signals</span></a>
          <a className={styles.navLink} href="#"><span className={styles.navIcon}>▤</span><span className={styles.navText}>Evidence</span></a>
          <a className={styles.navLink} href="#"><span className={styles.navIcon}>▥</span><span className={styles.navText}>Evaluation</span></a>
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

        <div className={styles.content}>
          <div className={styles.prototypeNote}>Concept prototype — the event structure and counts shown here are illustrative pending backend integration.</div>
          <div className={styles.breadcrumb}><Link href="/demo">Dashboard</Link> › Threats › Hantavirus</div>
          <div className={styles.pageHead}>
            <div>
              <h1>Hantavirus <span className={`${styles.pill} ${styles.pillActive}`}>Active</span></h1>
              <p className={styles.subtitle}>Tierra del Fuego, Argentina · May–September 2026</p>
            </div>
            <div className={styles.actions}><Link className={styles.button} href="/demo">← Dashboard</Link><button className={`${styles.button} ${styles.buttonPrimary}`}>Export report</button></div>
          </div>

          <div className={styles.filters}>
            <input value="01 May 2026 – 30 Sep 2026" readOnly aria-label="Date range" />
            <select value={domain} onChange={(event) => setDomain(event.target.value)} aria-label="One Health domain"><option value="all">All domains</option><option value="human">Human</option><option value="animal">Animal</option><option value="environment">Environment</option></select>
            <select aria-label="Signal type"><option>All signal types</option><option>Human case</option><option>Laboratory result</option><option>Environmental finding</option></select>
            <select aria-label="Source type"><option>All sources</option><option>Scientific publication</option><option>Health authority</option></select>
            <select aria-label="Location"><option>All locations</option><option>Ushuaia</option><option>Río Grande</option></select>
          </div>

          <div className={styles.threatLayout}>
            <section className={styles.card}>
              <h2>Timeline ({filtered.length} visible signals)</h2>
              <div className={styles.timeline}>
                {filtered.map((signal) => {
                  const originalIndex = signals.indexOf(signal);
                  return (
                    <button key={`${signal.date}-${signal.name}`} className={`${styles.timelineItem} ${selected === originalIndex ? styles.timelineSelected : ""}`} onClick={() => setSelected(originalIndex)}>
                      <div className={styles.timelineLine}><span className={`${styles.timelineNode} ${signal.color}`} /></div>
                      <div className={styles.timelineDate}>{signal.date}</div>
                      <div><div className={styles.signalName}>{signal.name}</div><div className={styles.signalText}>{signal.text}</div></div>
                    </button>
                  );
                })}
              </div>
              <div className={styles.detailPanel}><strong>Selected:</strong> {selectedSignal.name}<br />{selectedSignal.text}</div>
            </section>

            <section className={styles.card}>
              <h2>Geographic distribution</h2>
              <div className={styles.map}>
                <div className={styles.continent} />
                <span className={`${styles.marker} ${styles.markerHuman}`} style={{ left: "62%", top: "70%" }} />
                <span className={`${styles.marker} ${styles.markerAnimal}`} style={{ left: "59%", top: "66%" }} />
                <span className={`${styles.marker} ${styles.markerEnv}`} style={{ left: "54%", top: "48%" }} />
                <span className={`${styles.marker} ${selectedSignal.domain === "human" ? styles.markerHuman : selectedSignal.domain === "animal" ? styles.markerAnimal : styles.markerEnv}`} style={{ left: selectedSignal.location === "Ushuaia" ? "62%" : "57%", top: selectedSignal.location === "Ushuaia" ? "70%" : "51%", width: 29, height: 29, zIndex: 4 }} />
                <div className={styles.legend}><div><span className={`${styles.dot} ${styles.dotHuman}`} />Human</div><div><span className={`${styles.dot} ${styles.dotAnimal}`} />Animal</div><div><span className={`${styles.dot} ${styles.dotEnv}`} />Environment</div></div>
              </div>
              <div className={styles.detailPanel}><strong>{selectedSignal.location}</strong><br />Selected signal: {selectedSignal.name}</div>
            </section>

            <aside style={{ display: "grid", gap: 14, alignContent: "start" }}>
              <section className={styles.card}>
                <h2>Threat summary</h2>
                <div className={styles.summaryList}>
                  <div className={styles.summaryRow}><div className={styles.summaryKey}>Pathogen</div><div>Hantavirus (Andes virus)</div></div>
                  <div className={styles.summaryRow}><div className={styles.summaryKey}>Region</div><div>Tierra del Fuego, Argentina</div></div>
                  <div className={styles.summaryRow}><div className={styles.summaryKey}>Domains</div><div>Human · Animal · Environment</div></div>
                  <div className={styles.summaryRow}><div className={styles.summaryKey}>Signals</div><div>12</div></div>
                  <div className={styles.summaryRow}><div className={styles.summaryKey}>Independent sources</div><div>5</div></div>
                  <div className={styles.summaryRow}><div className={styles.summaryKey}>Status</div><div><span className={`${styles.pill} ${styles.pillActive}`}>Active</span></div></div>
                </div>
              </section>
              <section className={styles.card}>
                <h2>Key insights</h2>
                <ul className={styles.insights}><li>Animal signals precede later human findings in this demonstration scenario.</li><li>Environmental evidence broadens the event context.</li><li>Multiple independent sources contribute to the same threat view.</li></ul>
              </section>
              <section className={styles.card}>
                <h2>Next step</h2>
                <p className={`${styles.small} ${styles.muted}`}>Open the laboratory signal to inspect evidence and traceability.</p>
                <a className={`${styles.button} ${styles.buttonPrimary}`} href="#">Signal Detail →</a>
              </section>
            </aside>
          </div>
        </div>
      </main>
    </div>
  );
}
