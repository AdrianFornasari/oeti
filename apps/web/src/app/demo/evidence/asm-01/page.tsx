import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { ushuaiaRodentContext, ushuaiaRodentSignal } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

const claims = [
  {
    id: ushuaiaRodentSignal.directClaim.id,
    kind: "diagnostic_result",
    polarity: "positive",
    summary: ushuaiaRodentSignal.summary,
    evidence: ushuaiaRodentSignal.evidence,
  },
  {
    id: ushuaiaRodentContext.causalNegativeSignal.claimId,
    kind: "transmission_statement",
    polarity: "negative",
    summary: ushuaiaRodentContext.causalNegativeSignal.summary,
    evidence: ushuaiaRodentContext.causalNegativeSignal.evidence,
  },
  {
    id: ushuaiaRodentContext.samplingSignal.claimId,
    kind: "wildlife_sampling",
    polarity: "positive",
    summary: ushuaiaRodentContext.samplingSignal.summary,
    evidence: "Cabe destacar que durante esos operativos se capturaron 144 roedores.",
  },
];

export default function EvidenceTraceabilityPage() {
  const signal = ushuaiaRodentSignal;

  return (
    <DemoShell active="evidence">
      <div className={styles.content}>
        <PrototypeNote>This traceability view now reflects real atomic claims and signals from the 29 June 2026 ANLIS-Malbrán document in the MV Hondius evaluation corpus.</PrototypeNote>
        <div className={styles.breadcrumb}><Link href="/demo/signals/asm-01">Signals</Link> › {signal.shortId} › Evidence Traceability</div>
        <div className={styles.pageHead}>
          <div><h1>Evidence Traceability</h1><p className={styles.subtitle}>From official source text to atomic claims to assembled signal.</p></div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/signals/asm-01">← Back to signal</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/review/asm-01">Analyst review →</Link></div>
        </div>

        <section className={styles.grid4}>
          <article className={styles.card}><h3>1. Source document</h3><strong>ANLIS-Malbrán official news</strong><p className={`${styles.small} ${styles.muted}`}>29 June 2026</p></article>
          <article className={styles.card}><h3>2. Atomic claims</h3><strong>Claims c1, c4 and c5</strong><p className={`${styles.small} ${styles.muted}`}>Positive finding + negative causal evidence + wildlife sampling</p></article>
          <article className={styles.card}><h3>3. Signal assembly</h3><strong>Deterministic assembly</strong><p className={`${styles.small} ${styles.muted}`}>Atomic claims are assembled into distinct signals</p></article>
          <article className={styles.card}><h3>4. Interpretation</h3><strong>Finding ≠ outbreak source</strong><p className={`${styles.small} ${styles.muted}`}>The analysed rodents were ruled out as the infection source</p></article>
        </section>

        <div className={styles.threatLayout} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>Source document</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Source</div><div>{signal.source.label}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Publication date</div><div>{signal.documentDate}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Source code</div><div>{signal.source.code}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Evaluation case</div><div>ARG-HANTA-MV-HONDIUS-2026</div></div>
            </div>
            <div style={{ marginTop: 14, background: "#f8fafc", border: "1px solid #dce6f0", borderRadius: 10, padding: 16, lineHeight: 1.65 }}>
              <strong>Evidence excerpt</strong><p>“{signal.evidence}”</p>
            </div>
          </section>

          <section className={styles.card}>
            <h2>Atomic claims</h2>
            <div style={{ display: "grid", gap: 10 }}>
              {claims.map((claim) => (
                <article key={claim.id} style={{ border: "1px solid #dce6f0", borderRadius: 10, padding: 12 }}>
                  <strong>Claim {claim.id}</strong>
                  <div className={`${styles.small} ${styles.muted}`} style={{ margin: "7px 0" }}>{claim.kind} · polarity: {claim.polarity}</div>
                  <div className={styles.small}><strong>{claim.summary}</strong></div>
                  <div className={`${styles.small} ${styles.muted}`} style={{ marginTop: 7 }}>“{claim.evidence}”</div>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.card}>
            <h2>What OETI preserves</h2>
            <ol className={styles.insights}>
              <li>Positive wildlife evidence: five <em>Abrothrix</em> rodents had hantavirus-specific antibodies.</li>
              <li>Sampling context: 144 wild rodents were captured during operations from 18–22 May.</li>
              <li>Negative causal evidence: the analysed rodents were ruled out as the source linked to the MV Hondius event.</li>
            </ol>
            <pre style={{ whiteSpace: "pre-wrap", overflow: "auto", background: "#0d2b4b", color: "#dcecff", padding: 14, borderRadius: 10, fontSize: 11, lineHeight: 1.5 }}>{`{
  "signal_type": "laboratory_result",
  "signal_role": "primary_event",
  "domains": ["wildlife"],
  "host": "Abrothrix",
  "seropositive_animals": 5,
  "location": "Ushuaia",
  "extraction_confidence": 0.80,
  "causal_link_to_mv_hondius": "refuted"
}`}</pre>
          </section>
        </div>
      </div>
    </DemoShell>
  );
}
