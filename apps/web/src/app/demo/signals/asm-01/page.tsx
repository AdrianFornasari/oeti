import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { ushuaiaRodentContext, ushuaiaRodentSignal } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

const related = [
  ["29 Jun 2026", "ASM-02", ushuaiaRodentContext.genomicSignal.summary, "Wildlife + Genomic", "Genomic observation", "Reported"],
  ["29 Jun 2026", "ASM-03", ushuaiaRodentContext.causalNegativeSignal.summary, "Human + Wildlife", "Negative evidence", "Reported"],
  ["18–22 May 2026", "ASM-04", ushuaiaRodentContext.samplingSignal.summary, "Wildlife", "Wildlife event", "Reported"],
];

export default function SignalDetailPage() {
  const signal = ushuaiaRodentSignal;

  return (
    <DemoShell active="signals">
      <div className={styles.content}>
        <PrototypeNote>This screen now uses a real OETI v0.4.4 extraction from the MV Hondius evaluation corpus. Presentation labels remain simplified for sponsor use.</PrototypeNote>
        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">Threats</Link> › Hantavirus › Signal {signal.shortId}</div>
        <div className={styles.pageHead}>
          <div>
            <h1>5 Abrothrix rodents with hantavirus-specific antibodies</h1>
            <p className={styles.subtitle}>Signal {signal.shortId} · {signal.signalType} · {signal.signalRole} · Wildlife</p>
          </div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/threats/hantavirus">← Threat</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/evidence/asm-01">Trace this signal →</Link></div>
        </div>

        <div className={styles.threatLayout}>
          <section className={styles.card}>
            <h2>Summary</h2>
            <p>{signal.summary}</p>
            <div className={styles.detailPanel}><strong>Important interpretation</strong><br />This is a real wildlife signal detected during the investigation, but OETI also extracted negative evidence ruling out these analysed rodents as the infection source for the MV Hondius outbreak.</div>
          </section>

          <section className={styles.card}>
            <h2>Context</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Document date</div><div>{signal.documentDate}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Event date</div><div>Not stated in this signal</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Location</div><div>{signal.location.locality}, {signal.location.admin1}, {signal.location.country}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Geographic precision</div><div>{signal.location.precision}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Domain</div><div><span className={`${styles.pill} ${styles.pillAnimal}`}>Wildlife</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Verification</div><div>{signal.verificationStatus}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Extraction confidence</div><div>{Math.round(signal.extractionConfidence * 100)}%</div></div>
            </div>
          </section>

          <aside className={styles.card}>
            <h2>Signal traceability</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>1. Source</div><div>{signal.source.label}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>2. Atomic claim</div><div>{signal.directClaim.id}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>3. Assembly</div><div>Deterministic</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>4. Signal</div><div>{signal.signalType}</div></div>
            </div>
            <div style={{ marginTop: 14 }}><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/evidence/asm-01">Open traceability</Link></div>
          </aside>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Structured fields</h2>
            <table className={styles.table}><tbody>
              <tr><td>Seropositive animals</td><td><strong>{signal.metric.value}</strong></td></tr>
              <tr><td>Host / genus</td><td><strong>{signal.host}</strong></td></tr>
              <tr><td>Pathogen</td><td><strong>{signal.pathogen}</strong></td></tr>
              <tr><td>Test type</td><td><strong>{signal.diagnostics.testType}</strong></td></tr>
              <tr><td>Target</td><td><strong>{signal.diagnostics.target}</strong></td></tr>
              <tr><td>Result</td><td><strong>{signal.diagnostics.result}</strong></td></tr>
            </tbody></table>
          </section>
          <section className={styles.card}>
            <h2>Evidence excerpt</h2>
            <blockquote style={{ margin: 0, padding: 16, background: "#f5f9fd", borderRadius: 10, lineHeight: 1.55 }}>“{signal.evidence}”</blockquote>
            <p className={`${styles.small} ${styles.muted}`}>{signal.source.label} · official source included in the evaluation corpus.</p>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>Related extracted signals from the same document</h2>
          <table className={styles.table}>
            <thead><tr><th>Date</th><th>Signal ID</th><th>Description</th><th>Domain</th><th>Type</th><th>Status</th></tr></thead>
            <tbody>{related.map((row) => <tr key={row[1]}>{row.map((cell, index) => <td key={`${row[1]}-${index}`}>{cell}</td>)}</tr>)}</tbody>
          </table>
        </section>
      </div>
    </DemoShell>
  );
}
