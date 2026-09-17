"use client";

import Link from "next/link";
import { useState } from "react";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import styles from "../../demo.module.css";

type Decision = "confirm" | "correct" | "reject" | null;

export default function AnalystReviewPage() {
  const [decision, setDecision] = useState<Decision>(null);
  const [submitted, setSubmitted] = useState(false);

  return (
    <DemoShell active="evaluation">
      <div className={styles.content}>
        <PrototypeNote>Concept prototype — analyst actions on this page are simulated and do not write to the production database.</PrototypeNote>
        <div className={styles.breadcrumb}><Link href="/demo/evidence/asm-01">Evidence</Link> › Analyst Review › Signal ASM-01</div>
        <div className={styles.pageHead}>
          <div><h1>Analyst Review</h1><p className={styles.subtitle}>Validate, correct or reject a system-extracted signal.</p></div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/evidence/asm-01">← Evidence</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/evaluation">System evaluation →</Link></div>
        </div>

        <section className={styles.card}>
          <div className={styles.pageHead} style={{ marginBottom: 0 }}>
            <div><div className={styles.small}>SIGNAL ASM-01</div><h2 style={{ marginTop: 4 }}>Serology: 5 Abrothrix rodents positive for hantavirus</h2></div>
            <div><span className={`${styles.pill} ${styles.pillAnimal}`}>Animal</span> <span className={`${styles.pill} ${styles.pillActive}`}>New</span></div>
          </div>
        </section>

        <div className={styles.threatLayout} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>Extracted information</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Summary</div><div>Five Abrothrix rodents with specific antibodies against hantavirus.</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Date</div><div>14 May 2026</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Location</div><div>Ushuaia, Tierra del Fuego, Argentina</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Signal type</div><div>Laboratory result</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Signal role</div><div>Primary event</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Source</div><div>Smith et al. (2026)</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Metrics</div><div>5 positive / 12 sampled · 41.7%</div></div>
            </div>
          </section>

          <section className={styles.card}>
            <h2>Evidence excerpt</h2>
            <blockquote style={{ margin: 0, background: "#f5f9fd", borderRadius: 10, padding: 16, lineHeight: 1.6 }}>“Five rodents of the genus Abrothrix showed specific antibodies against hantavirus, with a seroprevalence of 41.7% (5/12).”</blockquote>
            <h2 style={{ marginTop: 18 }}>Analyst assessment</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 9 }}>
              <button className={styles.button} style={{ background: decision === "confirm" ? "#e8f8ec" : undefined, borderColor: "#65bd7e" }} onClick={() => { setDecision("confirm"); setSubmitted(false); }}>✓ Confirm</button>
              <button className={styles.button} style={{ background: decision === "correct" ? "#fff3d5" : undefined, borderColor: "#e9b64d" }} onClick={() => { setDecision("correct"); setSubmitted(false); }}>✎ Correct</button>
              <button className={styles.button} style={{ background: decision === "reject" ? "#ffe7e7" : undefined, borderColor: "#ef7b7b" }} onClick={() => { setDecision("reject"); setSubmitted(false); }}>✕ Reject</button>
            </div>
            <textarea aria-label="Review comment" placeholder="Add a comment…" style={{ width: "100%", minHeight: 90, marginTop: 12, border: "1px solid #dce6f0", borderRadius: 9, padding: 10, font: "inherit" }} />
            <button disabled={!decision} className={`${styles.button} ${styles.buttonPrimary}`} style={{ marginTop: 10, opacity: decision ? 1 : .5 }} onClick={() => setSubmitted(true)}>Submit review</button>
            {submitted && <div className={styles.detailPanel}><strong>Review recorded in demo state.</strong><br />Decision: {decision}. In the production design this would create a review record and audit trail.</div>}
          </section>

          <aside style={{ display: "grid", gap: 14, alignContent: "start" }}>
            <section className={styles.card}><h2>Source document</h2><strong>Smith et al. (2026)</strong><p className={`${styles.small} ${styles.muted}`}>Scientific publication · demonstration source</p><Link className={styles.button} href="/demo/evidence/asm-01">View evidence</Link></section>
            <section className={styles.card}><h2>Review history</h2><div className={styles.summaryList}><div className={styles.summaryRow}><div className={styles.summaryKey}>14 May</div><div>New · extracted automatically</div></div><div className={styles.summaryRow}><div className={styles.summaryKey}>15 May</div><div>Assigned for analyst review</div></div></div></section>
            <section className={styles.card}><h2>Analyst guidance</h2><ul className={styles.insights}><li>Verify that the source supports the extracted information.</li><li>Check date, location and One Health domain.</li><li>Prefer correction to rejection for minor errors.</li></ul></section>
          </aside>
        </div>
      </div>
    </DemoShell>
  );
}
