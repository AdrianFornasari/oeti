import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import styles from "../../demo.module.css";

const related = [
  ["04 May 2026", "ASM-02", "Confirmed human case in crew member", "Human", "Human case", "Reviewed"],
  ["10 May 2026", "ASM-03", "Rodent investigation initiated", "Animal", "Investigation", "Reviewed"],
  ["22 May 2026", "ASM-04", "Environmental sampling in soil", "Environment", "Environmental sampling", "New"],
];

export default function SignalDetailPage() {
  return (
    <DemoShell active="signals">
      <div className={styles.content}>
        <PrototypeNote>Concept prototype — this signal is a demonstration record used to show the intended OETI workflow.</PrototypeNote>
        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">Threats</Link> › Hantavirus › Signal ASM-01</div>
        <div className={styles.pageHead}>
          <div>
            <h1>Serology: 5 Abrothrix rodents positive for hantavirus</h1>
            <p className={styles.subtitle}>Signal ASM-01 · Laboratory result · Primary event · Animal</p>
          </div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/threats/hantavirus">← Threat</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/evidence/asm-01">Trace this signal →</Link></div>
        </div>

        <div className={styles.threatLayout}>
          <section className={styles.card}>
            <h2>Summary</h2>
            <p>Serological analysis detected specific antibodies against hantavirus in five rodents of the genus <em>Abrothrix</em> collected in Ushuaia, Tierra del Fuego.</p>
            <div className={styles.detailPanel}><strong>Key point</strong><br />Evidence of hantavirus circulation in a local rodent population.</div>
          </section>

          <section className={styles.card}>
            <h2>Context</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Date</div><div>14 May 2026</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Location</div><div>Ushuaia, Tierra del Fuego, Argentina</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Geographic precision</div><div>Locality</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>One Health domain</div><div><span className={`${styles.pill} ${styles.pillAnimal}`}>Animal</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Source type</div><div>Scientific publication</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Confidence</div><div><span className={`${styles.pill} ${styles.pillReviewed}`}>High</span></div></div>
            </div>
          </section>

          <aside className={styles.card}>
            <h2>Signal traceability</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>1. Source</div><div>Smith et al. (2026)</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>2. Atomic claims</div><div>#17 · #18 · #21</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>3. Assembly</div><div>Deterministic</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>4. Signal</div><div>Laboratory result</div></div>
            </div>
            <div style={{ marginTop: 14 }}><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/evidence/asm-01">Open traceability</Link></div>
          </aside>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Structured metrics</h2>
            <table className={styles.table}><tbody>
              <tr><td>Serology positive animals</td><td><strong>5</strong></td></tr>
              <tr><td>Total rodents sampled</td><td><strong>12</strong></td></tr>
              <tr><td>Species / genus</td><td><strong>Abrothrix sp.</strong></td></tr>
              <tr><td>Test type</td><td><strong>IgG ELISA</strong></td></tr>
              <tr><td>Seroprevalence</td><td><strong>41.7%</strong></td></tr>
            </tbody></table>
          </section>
          <section className={styles.card}>
            <h2>Evidence excerpt</h2>
            <blockquote style={{ margin: 0, padding: 16, background: "#f5f9fd", borderRadius: 10, lineHeight: 1.55 }}>
              “Five rodents of the genus Abrothrix showed specific antibodies against hantavirus, with a seroprevalence of 41.7% (5/12).”
            </blockquote>
            <p className={`${styles.small} ${styles.muted}`}>Smith et al. (2026). Demonstration citation used in the prototype.</p>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>Related signals</h2>
          <table className={styles.table}>
            <thead><tr><th>Date</th><th>Signal ID</th><th>Description</th><th>Domain</th><th>Type</th><th>Status</th></tr></thead>
            <tbody>{related.map((row) => <tr key={row[1]}>{row.map((cell, index) => <td key={`${row[1]}-${index}`}>{cell}</td>)}</tr>)}</tbody>
          </table>
        </section>
      </div>
    </DemoShell>
  );
}
