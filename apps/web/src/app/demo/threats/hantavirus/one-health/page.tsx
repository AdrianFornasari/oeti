import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../../demo-shell";
import { mvHondiusBenchmark } from "../../../mv-hondius-data";
import styles from "../../../demo.module.css";

const domainRows = [
  {
    domain: "Human",
    tone: styles.pillHuman,
    evidence: "Cluster, confirmed/probable cases, deaths and probable person-to-person transmission aboard MV Hondius.",
    documents: "04 May · 12 May · 19 May · 26 May",
    status: "Strong direct evidence",
  },
  {
    domain: "Wildlife",
    tone: styles.pillAnimal,
    evidence: "Field investigations in Ushuaia and Malargüe, including seropositive Abrothrix rodents and negative rodent serology.",
    documents: "19 May · 29 Jun · 08 Jul",
    status: "Positive + negative evidence",
  },
  {
    domain: "Genomic",
    tone: styles.pillEnv,
    evidence: "Andes-virus characterization and a distinct Orthohantavirus andesense variant in Ushuaia wildlife; genomic context helped refute a simple causal link.",
    documents: "12 May · 19 May · 26 May · 29 Jun",
    status: "Relationship-testing evidence",
  },
  {
    domain: "Mobility",
    tone: styles.pillMedium,
    evidence: "Travel history in Malargüe retained as contextual exposure history, not as a confirmed infection location.",
    documents: "08 Jul",
    status: "Contextual evidence",
  },
];

const convergenceRows = mvHondiusBenchmark.documents.map((doc) => ({
  date: doc.date,
  label: doc.label,
  human: doc.domains.includes("human"),
  wildlife: doc.domains.includes("wildlife"),
  genomic: doc.domains.includes("genomic"),
  mobility: doc.domains.includes("mobility"),
  relation: doc.relation,
}));

export default function OneHealthConvergencePage() {
  return (
    <DemoShell active="threats">
      <div className={styles.content}>
        <PrototypeNote>
          Real-case One Health view — this screen uses only domains and relationships adjudicated in the six-document MV Hondius gold-standard corpus. No environmental-domain signal is added because none is adjudicated in this corpus.
        </PrototypeNote>

        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">Threats</Link> › MV Hondius › One Health View</div>
        <div className={styles.pageHead}>
          <div>
            <h1>MV Hondius — One Health evidence convergence</h1>
            <p className={styles.subtitle}>Human · Wildlife · Genomic · Mobility evidence, including negative and refuted findings.</p>
          </div>
          <div className={styles.actions}>
            <Link className={styles.button} href="/demo/threats/hantavirus">← Threat Explorer</Link>
            <Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/signals/asm-01">Open wildlife signal →</Link>
          </div>
        </div>

        <section className={styles.grid4}>
          {domainRows.map((row) => (
            <article className={styles.card} key={row.domain}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start" }}>
                <h3>{row.domain}</h3>
                <span className={`${styles.pill} ${row.tone}`}>{row.status}</span>
              </div>
              <p className={styles.small}>{row.evidence}</p>
              <div className={`${styles.small} ${styles.muted}`}>Documents: {row.documents}</div>
            </article>
          ))}
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Convergence model</h2>
            <div style={{ display: "grid", gap: 12 }}>
              <div style={{ padding: 16, borderRadius: 12, background: "#eef5ff", border: "1px solid #cfe0f7" }}>
                <strong>Human outbreak evidence</strong>
                <p className={styles.small}>The event begins as a human outbreak signal: cluster, deaths, confirmed/probable cases and later a probable person-to-person transmission hypothesis.</p>
              </div>
              <div style={{ padding: 16, borderRadius: 12, background: "#eef9f0", border: "1px solid #cfe8d5" }}>
                <strong>Wildlife investigation</strong>
                <p className={styles.small}>Wildlife data add biological plausibility and local circulation evidence, but they do not automatically identify the outbreak source.</p>
              </div>
              <div style={{ padding: 16, borderRadius: 12, background: "#f3efff", border: "1px solid #dcd1fb" }}>
                <strong>Genomic discrimination</strong>
                <p className={styles.small}>Genomic findings help compare relationships between human and wildlife viruses and prevent an unsupported causal linkage.</p>
              </div>
              <div style={{ padding: 16, borderRadius: 12, background: "#fff7e7", border: "1px solid #f1dfb6" }}>
                <strong>Mobility context</strong>
                <p className={styles.small}>Travel history supplies epidemiological context, but OETI keeps it separate from confirmed exposure.</p>
              </div>
              <div className={styles.detailPanel}>
                <strong>One Health conclusion</strong><br />The analytical value is not a numeric “One Health score”; it is the explicit reconciliation of cross-domain evidence, uncertainty, negative results and refuted hypotheses.
              </div>
            </div>
          </section>

          <section className={styles.card}>
            <h2>Critical relationships</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Human ↔ Human</div><div>Person-to-person transmission aboard the vessel: <strong>probable</strong>, not confirmed.</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Wildlife → Human</div><div>For the analysed Ushuaia rodents, the outbreak-source relationship was <strong>refuted</strong>.</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Genomic ↔ Outbreak</div><div>Genomic similarity/difference informs relatedness but is not treated as proof of geographic origin.</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Mobility ↔ Exposure</div><div>Malargüe is retained as travel history; confirmed exposure remains unresolved.</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Environment</div><div>No environmental-domain signal is adjudicated in this six-document corpus.</div></div>
            </div>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>Cross-domain document matrix</h2>
          <table className={styles.table}>
            <thead>
              <tr><th>Date</th><th>Document</th><th>Human</th><th>Wildlife</th><th>Genomic</th><th>Mobility</th><th>Evidence role</th></tr>
            </thead>
            <tbody>
              {convergenceRows.map((row) => (
                <tr key={row.date}>
                  <td>{row.date}</td>
                  <td>{row.label}</td>
                  <td>{row.human ? "●" : "—"}</td>
                  <td>{row.wildlife ? "●" : "—"}</td>
                  <td>{row.genomic ? "●" : "—"}</td>
                  <td>{row.mobility ? "●" : "—"}</td>
                  <td>{row.relation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>Why the convergence matters</h2>
          <ul className={styles.insights}>
            <li>The same investigation can contain simultaneously true positive findings and true negative findings.</li>
            <li>Cross-domain proximity does not equal causality: seropositive wildlife in Ushuaia did not establish the source of the human outbreak.</li>
            <li>Genomics helps discriminate relatedness and prevents overinterpretation of geographic coincidence.</li>
            <li>Travel history remains useful even when it does not resolve the exposure location.</li>
            <li>OETI should surface uncertainty explicitly instead of forcing every signal into a single explanatory narrative.</li>
          </ul>
        </section>
      </div>
    </DemoShell>
  );
}
