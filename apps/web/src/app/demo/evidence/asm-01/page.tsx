import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import styles from "../../demo.module.css";

const claims = [
  { id: "#17", subject: "Abrothrix rodents", predicate: "sampled_count", object: "12", evidence: "A total of 12 rodents of the genus Abrothrix were captured in the Ushuaia area." },
  { id: "#18", subject: "Abrothrix rodents", predicate: "serology_positive", object: "5", evidence: "Five individuals showed specific antibodies against hantavirus by IgG ELISA." },
  { id: "#21", subject: "seroprevalence", predicate: "value", object: "41.7% (5/12)", evidence: "...with a seroprevalence of 41.7% (5/12)." },
];

export default function EvidenceTraceabilityPage() {
  return (
    <DemoShell active="evidence">
      <div className={styles.content}>
        <PrototypeNote>Concept prototype — source text and claim identifiers are demonstration content for the sponsor walkthrough.</PrototypeNote>
        <div className={styles.breadcrumb}><Link href="/demo/signals/asm-01">Signals</Link> › ASM-01 › Evidence Traceability</div>
        <div className={styles.pageHead}>
          <div><h1>Evidence Traceability</h1><p className={styles.subtitle}>From source document to atomic claims to assembled signal.</p></div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/signals/asm-01">← Back to signal</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/review/asm-01">Analyst review →</Link></div>
        </div>

        <section className={styles.grid4}>
          <article className={styles.card}><h3>1. Source document</h3><strong>Scientific article</strong><p className={`${styles.small} ${styles.muted}`}>Smith et al. (2026)</p></article>
          <article className={styles.card}><h3>2. Atomic claims</h3><strong>3 relevant claims</strong><p className={`${styles.small} ${styles.muted}`}>Extracted from source spans</p></article>
          <article className={styles.card}><h3>3. Signal assembly</h3><strong>Deterministic assembly</strong><p className={`${styles.small} ${styles.muted}`}>Claims #17 + #18 + #21</p></article>
          <article className={styles.card}><h3>4. Resulting signal</h3><strong>Laboratory result</strong><p className={`${styles.small} ${styles.muted}`}>5 seropositive Abrothrix rodents</p></article>
        </section>

        <div className={styles.threatLayout} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>Source document</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Title</div><div>Serological evidence of hantavirus in Abrothrix rodents in Tierra del Fuego</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Publication date</div><div>14 May 2026</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Type</div><div>Scientific article</div></div>
            </div>
            <div style={{ marginTop: 14, background: "#f8fafc", border: "1px solid #dce6f0", borderRadius: 10, padding: 16, lineHeight: 1.65 }}>
              <strong>Results excerpt</strong><p>A total of 12 rodents of the genus <em>Abrothrix</em> were captured in the Ushuaia area. Five individuals showed specific antibodies against hantavirus by IgG ELISA, with a seroprevalence of 41.7% (5/12).</p>
            </div>
          </section>

          <section className={styles.card}>
            <h2>Atomic claims</h2>
            <div style={{ display: "grid", gap: 10 }}>
              {claims.map((claim) => (
                <article key={claim.id} style={{ border: "1px solid #dce6f0", borderRadius: 10, padding: 12 }}>
                  <strong>Claim {claim.id}</strong>
                  <div className={`${styles.small} ${styles.muted}`} style={{ margin: "7px 0" }}>{claim.subject} · {claim.predicate} · {claim.object}</div>
                  <div className={styles.small}>{claim.evidence}</div>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.card}>
            <h2>Signal assembly</h2>
            <ol className={styles.insights}>
              <li>Identify compatible claims sharing subject, location and event context.</li>
              <li>Apply deterministic assembly rules for a laboratory result.</li>
              <li>Generate a structured signal with harmonized fields and metrics.</li>
            </ol>
            <pre style={{ whiteSpace: "pre-wrap", overflow: "auto", background: "#0d2b4b", color: "#dcecff", padding: 14, borderRadius: 10, fontSize: 11, lineHeight: 1.5 }}>{`{
  "type": "laboratory_result",
  "subject": "Abrothrix rodents",
  "value": 5,
  "total_sampled": 12,
  "seroprevalence": 0.417,
  "location": "Ushuaia",
  "one_health_domain": "animal",
  "claims": ["#17", "#18", "#21"]
}`}</pre>
          </section>
        </div>
      </div>
    </DemoShell>
  );
}
