"use client";

import Link from "next/link";
import { useState } from "react";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { mvHondiusBenchmark } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

const relationTone = (relation: string) => {
  if (relation.includes("Negative")) return styles.pillLow;
  if (relation.includes("Transmission")) return styles.pillMedium;
  return styles.pillHigh;
};

const sourceFamilies = new Set(mvHondiusBenchmark.documents.map((doc) => doc.source)).size;

export default function HantavirusThreatPage() {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const selected = mvHondiusBenchmark.documents[selectedIndex] ?? mvHondiusBenchmark.documents[0];

  return (
    <DemoShell active="threats">
      <div className={styles.content}>
        <PrototypeNote>
          Real-case sponsor demo — the six timeline entries below come from the adjudicated MV Hondius gold-standard corpus. Document date, event/reference date and geographic role are shown separately to avoid false temporal or causal precision.
        </PrototypeNote>

        <div className={styles.breadcrumb}><Link href="/demo">Dashboard</Link> › Threats › MV Hondius hantavirus investigation</div>
        <div className={styles.pageHead}>
          <div>
            <h1>MV Hondius hantavirus investigation <span className={`${styles.pill} ${styles.pillReviewed}`}>Adjudicated corpus</span></h1>
            <p className={styles.subtitle}>Case {mvHondiusBenchmark.caseCode} · Gold-standard benchmark v{mvHondiusBenchmark.benchmarkVersion} · Six official-source documents</p>
          </div>
          <div className={styles.actions}>
            <Link className={styles.button} href="/demo">← Dashboard</Link>
            <Link className={styles.button} href="/demo/threats/hantavirus/one-health">One Health view</Link>
            <Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/signals/asm-01">Open wildlife signal →</Link>
          </div>
        </div>

        <section className={styles.grid4}>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.blue}`}>6</div>
            <div><span className={styles.metricValue}>6</span><div className={styles.metricLabel}>Adjudicated documents</div><small className={styles.muted}>04 May – 08 Jul 2026</small></div>
          </article>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.red}`}>11</div>
            <div><span className={styles.metricValue}>11</span><div className={styles.metricLabel}>Maximum identified cases</div><small className={styles.muted}>Reported by 13 May</small></div>
          </article>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.green}`}>9</div>
            <div><span className={styles.metricValue}>9</span><div className={styles.metricLabel}>Confirmed cases</div><small className={styles.muted}>Total reported by 26 May</small></div>
          </article>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.purple}`}>2</div>
            <div><span className={styles.metricValue}>2</span><div className={styles.metricLabel}>Negative-evidence investigations</div><small className={styles.muted}>Ushuaia causal link + Malargüe serology</small></div>
          </article>
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Gold-standard document timeline</h2>
            <p className={`${styles.small} ${styles.muted}`}>The vertical order is the document-publication sequence. The epidemiological event/reference date is displayed separately inside each entry.</p>
            <div className={styles.timeline}>
              {mvHondiusBenchmark.documents.map((doc, index) => (
                <button
                  key={doc.id}
                  className={`${styles.timelineItem} ${selectedIndex === index ? styles.timelineSelected : ""}`}
                  onClick={() => setSelectedIndex(index)}
                >
                  <div className={styles.timelineLine}><span className={`${styles.timelineNode} ${doc.relation.includes("Negative") ? styles.markerAnimal : styles.markerHuman}`} /></div>
                  <div className={styles.timelineDate}>{doc.date}</div>
                  <div>
                    <div className={styles.signalName}>{doc.label}</div>
                    <div className={styles.signalText}>{doc.summary}</div>
                    <div style={{ marginTop: 7, display: "flex", gap: 6, flexWrap: "wrap" }}>
                      <span className={`${styles.pill} ${relationTone(doc.relation)}`}>{doc.relation}</span>
                      <span className={styles.pill}>Event/reference: {doc.eventDate}</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section className={styles.card}>
            <h2>Selected document</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Document date</div><div><strong>{selected.date}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Event/reference date</div><div>{selected.eventDate}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Official source</div><div>{selected.sourceLabel} <span className={styles.muted}>({selected.source})</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Location context</div><div>{selected.location}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Location role</div><div>{selected.locationRole}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Evidence role</div><div><span className={`${styles.pill} ${relationTone(selected.relation)}`}>{selected.relation}</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Domains</div><div>{selected.domains.join(" · ")}</div></div>
            </div>

            <div className={styles.detailPanel} style={{ marginTop: 14 }}>
              <strong>Interpretation</strong><br />{selected.summary}
            </div>

            <h3 style={{ marginTop: 18 }}>Key adjudicated facts</h3>
            <ul className={styles.insights}>{selected.keyFacts.map((fact) => <li key={fact}>{fact}</li>)}</ul>

            <div style={{ marginTop: 16 }}>
              <a className={styles.button} href={selected.sourceUrl} target="_blank" rel="noreferrer">Open official source ↗</a>
            </div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Threat summary — adjudicated corpus</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Case</div><div>{mvHondiusBenchmark.caseCode}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Human outbreak</div><div>Andes-virus hantavirus aboard MV Hondius</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Peak identified count</div><div>11 cases by 13 May: 8 confirmed, 2 probable, 1 inconclusive</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Later confirmed total</div><div>9 confirmed + 2 probable by 26 May</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Transmission assessment</div><div>Person-to-person transmission aboard the vessel adjudicated as probable, not confirmed</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Wildlife evidence</div><div>Hantavirus detected in Abrothrix rodents in Ushuaia, but the analysed rodents were ruled out as the outbreak source</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Source families</div><div>{sourceFamilies}: Ministerio de Salud / BEN and ANLIS-Malbrán</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Benchmark status</div><div><span className={`${styles.pill} ${styles.pillReviewed}`}>6/6 documents adjudicated</span></div></div>
            </div>
          </section>

          <section className={styles.card}>
            <h2>Key insights — evidence evolution</h2>
            <ul className={styles.insights}>
              <li><strong>The outbreak signal strengthened over time:</strong> the corpus progresses from one laboratory-confirmed passenger and three deaths to 11 identified cases by 13 May, then nine confirmed and two probable cases by 26 May.</li>
              <li><strong>Transmission remains qualified:</strong> the 19 May BEN supports probable person-to-person transmission aboard the vessel; OETI should preserve “probable” rather than promote it to confirmed.</li>
              <li><strong>Positive wildlife evidence did not establish causality:</strong> five Abrothrix rodents in Ushuaia were seropositive and a related Orthohantavirus andesense variant was characterized, yet the analysed rodents were explicitly ruled out as the source of the human outbreak.</li>
              <li><strong>Negative evidence changes the investigation:</strong> Malargüe rodent serology was negative, so travel history remains contextual evidence rather than a confirmed exposure location.</li>
              <li><strong>No environmental-domain signal is adjudicated in this six-document corpus:</strong> the One Health value here comes from integrating human, wildlife, genomic and mobility evidence, including negative findings.</li>
            </ul>
            <div className={styles.detailPanel}>
              <strong>OETI analytical principle</strong><br />Positive findings, negative findings, uncertainty and refuted hypotheses must coexist in the same threat model without being flattened into a single causal story.
            </div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Geographic context — roles, not inferred origins</h2>
            <div className={styles.threatList}>
              {mvHondiusBenchmark.geographicContext.map((item) => (
                <article className={styles.threatItem} key={item.place}>
                  <div><strong>{item.place}</strong><div className={`${styles.small} ${styles.muted}`}>{item.role}</div><div className={styles.small} style={{ marginTop: 5 }}>{item.note}</div></div>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.card}>
            <h2>What changed across the investigation</h2>
            <ul className={styles.insights}>
              <li>The 4 May source established the cluster, deaths and a laboratory-confirmed hantavirus case.</li>
              <li>The BEN updates progressively increased the case count and, by 19 May, supported probable person-to-person transmission aboard the vessel.</li>
              <li>The Tierra del Fuego wildlife investigation found genuine hantavirus evidence in Abrothrix rodents, but genomic/epidemiological analysis refuted those analysed rodents as the source of the MV Hondius outbreak.</li>
              <li>The Malargüe investigation added negative wildlife evidence and preserved the location as travel history rather than confirmed exposure.</li>
            </ul>
            <div className={styles.detailPanel}>
              <strong>Why this matters for OETI</strong><br />The system must integrate positive, negative and contextual evidence without collapsing them into a single causal narrative.
            </div>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>Corpus overview</h2>
          <table className={styles.table}>
            <thead><tr><th>Document date</th><th>Document</th><th>Source</th><th>Evidence role</th><th>Geographic context</th></tr></thead>
            <tbody>
              {mvHondiusBenchmark.documents.map((doc) => (
                <tr key={doc.id}><td>{doc.date}</td><td>{doc.label}</td><td>{doc.sourceLabel}</td><td>{doc.relation}</td><td>{doc.location}</td></tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </DemoShell>
  );
}
