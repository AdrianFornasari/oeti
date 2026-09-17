"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { ushuaiaRodentContext, ushuaiaRodentSignal } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

type Decision = "confirm" | "correct" | "reject" | null;

const decisionDetails = {
  confirm: {
    title: "Confirm signal",
    status: "analyst_confirmed",
    summary: "The assembled signal is accepted as supported by the cited atomic claim.",
    effects: [
      "Keep atomic claim c1 unchanged.",
      "Keep ASM-01 in the operational signal set.",
      "Record an analyst confirmation in the audit trail.",
      "Do not infer that these rodents caused the MV Hondius outbreak; claim c4 still refutes that link for the analysed rodents.",
    ],
  },
  correct: {
    title: "Correct signal",
    status: "analyst_corrected",
    summary: "The source evidence is retained while analyst-entered corrections are applied as an auditable override.",
    effects: [
      "Preserve the original atomic claim and source text.",
      "Store the analyst correction separately from the machine extraction.",
      "Flag the signal for deterministic reassembly / downstream refresh.",
      "Keep independent negative causal evidence (claim c4) intact.",
    ],
  },
  reject: {
    title: "Reject signal",
    status: "analyst_rejected",
    summary: "The source and extracted claim remain traceable, but this assembled signal would not be used operationally as accepted intelligence.",
    effects: [
      "Preserve the source document and original extraction for auditability.",
      "Mark ASM-01 as rejected by an analyst.",
      "Exclude the rejected signal from accepted downstream intelligence views.",
      "Do not delete related claims or independent signals from the same document.",
    ],
  },
} as const;

export default function AnalystReviewPage() {
  const signal = ushuaiaRodentSignal;
  const [decision, setDecision] = useState<Decision>(null);
  const [submitted, setSubmitted] = useState(false);
  const [comment, setComment] = useState("");
  const [correctedSummary, setCorrectedSummary] = useState(signal.summary);
  const [correctedType, setCorrectedType] = useState(signal.signalType);
  const [correctedRole, setCorrectedRole] = useState(signal.signalRole);

  const selectedDecision = useMemo(
    () => (decision ? decisionDetails[decision] : null),
    [decision],
  );

  const chooseDecision = (nextDecision: Exclude<Decision, null>) => {
    setDecision(nextDecision);
    setSubmitted(false);
  };

  return (
    <DemoShell active="evaluation">
      <div className={styles.content}>
        <PrototypeNote>
          Sponsor demo — review actions are held only in this browser state. No production database write is performed. The evidence and signal shown below come from the adjudicated MV Hondius corpus.
        </PrototypeNote>

        <div className={styles.breadcrumb}>
          <Link href="/demo/evidence/asm-01">Evidence</Link> › Analyst Review › Signal {signal.shortId}
        </div>

        <div className={styles.pageHead}>
          <div>
            <h1>Analyst Review</h1>
            <p className={styles.subtitle}>Human validation with explicit consequences for claims, signals and downstream intelligence.</p>
          </div>
          <div className={styles.actions}>
            <Link className={styles.button} href="/demo/evidence/asm-01">← Evidence</Link>
            <Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/evaluation">System evaluation →</Link>
          </div>
        </div>

        <section className={styles.card}>
          <div className={styles.pageHead} style={{ marginBottom: 0 }}>
            <div>
              <div className={styles.small}>REVIEW TARGET · SIGNAL {signal.shortId}</div>
              <h2 style={{ marginTop: 4 }}>5 <em>Abrothrix</em> rodents with hantavirus-specific antibodies</h2>
              <p className={`${styles.small} ${styles.muted}`} style={{ marginBottom: 0 }}>
                Assembled deterministically from atomic claim {signal.directClaim.id} · document dated {signal.documentDate}
              </p>
            </div>
            <div>
              <span className={`${styles.pill} ${styles.pillAnimal}`}>Wildlife</span>{" "}
              <span className={`${styles.pill} ${styles.pillActive}`}>Awaiting review</span>
            </div>
          </div>
        </section>

        <div className={styles.threatLayout} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>Extracted signal</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Summary</div><div>{signal.summary}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Document date</div><div>{signal.documentDate}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Event date</div><div>Not stated in this signal</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Location</div><div>{signal.location.locality}, {signal.location.admin1}, {signal.location.country}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Signal type</div><div>{signal.signalType}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Signal role</div><div>{signal.signalRole}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Source</div><div>{signal.source.label}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Metric</div><div>{signal.metric.value} seropositive animals</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Extraction confidence</div><div>{Math.round(signal.extractionConfidence * 100)}%</div></div>
            </div>

            <div className={styles.detailPanel} style={{ marginTop: 14 }}>
              <strong>Review guardrail</strong><br />
              Confirming this laboratory signal confirms only that the source supports the wildlife finding. It does <strong>not</strong> confirm that these rodents were the source of the MV Hondius outbreak.
            </div>
          </section>

          <section className={styles.card}>
            <h2>Evidence considered</h2>
            <div style={{ display: "grid", gap: 10 }}>
              <article style={{ border: "1px solid #dce6f0", borderRadius: 10, padding: 12 }}>
                <div className={styles.small}><strong>Claim c1 · positive diagnostic result</strong></div>
                <blockquote style={{ margin: "8px 0 0", lineHeight: 1.55 }}>“{signal.evidence}”</blockquote>
              </article>

              <article style={{ border: "1px solid #dce6f0", borderRadius: 10, padding: 12 }}>
                <div className={styles.small}><strong>Claim {ushuaiaRodentContext.samplingSignal.claimId} · sampling context</strong></div>
                <p style={{ marginBottom: 0 }}>{ushuaiaRodentContext.samplingSignal.summary}</p>
              </article>

              <article style={{ border: "1px solid #efc4c4", borderRadius: 10, padding: 12, background: "#fff8f8" }}>
                <div className={styles.small}><strong>Claim {ushuaiaRodentContext.causalNegativeSignal.claimId} · negative causal evidence</strong></div>
                <p style={{ marginBottom: 6 }}>{ushuaiaRodentContext.causalNegativeSignal.summary}</p>
                <div className={`${styles.small} ${styles.muted}`}>“{ushuaiaRodentContext.causalNegativeSignal.evidence}”</div>
              </article>
            </div>

            <div style={{ marginTop: 14 }}>
              <Link className={styles.button} href="/demo/evidence/asm-01">Open full traceability</Link>
            </div>
          </section>

          <aside style={{ display: "grid", gap: 14, alignContent: "start" }}>
            <section className={styles.card}>
              <h2>Provenance chain</h2>
              <div className={styles.summaryList}>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>1. Source</div><div>ANLIS-Malbrán</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>2. Claim</div><div>{signal.directClaim.id} · diagnostic_result</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>3. Assembly</div><div>Deterministic</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>4. Signal</div><div>{signal.shortId} · {signal.signalType}</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>5. Review</div><div>{submitted && selectedDecision ? selectedDecision.status : "Pending"}</div></div>
              </div>
            </section>

            <section className={styles.card}>
              <h2>Review state</h2>
              <p className={`${styles.small} ${styles.muted}`}>No fabricated review dates are shown. This panel represents the conceptual workflow only.</p>
              <div className={styles.summaryList}>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>Extraction</div><div>Machine generated</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>Analyst</div><div>{submitted ? "Decision recorded in demo state" : "Awaiting decision"}</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>Backend</div><div>Not written</div></div>
              </div>
            </section>
          </aside>
        </div>

        <div className={styles.dashboardMain} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>Analyst decision</h2>
            <p className={`${styles.small} ${styles.muted}`}>Choose what should happen to this assembled signal. The raw source and original extraction remain traceable in every path.</p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 9 }}>
              <button
                className={styles.button}
                style={{ background: decision === "confirm" ? "#e8f8ec" : undefined, borderColor: "#65bd7e" }}
                onClick={() => chooseDecision("confirm")}
              >
                ✓ Confirm
              </button>
              <button
                className={styles.button}
                style={{ background: decision === "correct" ? "#fff3d5" : undefined, borderColor: "#e9b64d" }}
                onClick={() => chooseDecision("correct")}
              >
                ✎ Correct
              </button>
              <button
                className={styles.button}
                style={{ background: decision === "reject" ? "#ffe7e7" : undefined, borderColor: "#ef7b7b" }}
                onClick={() => chooseDecision("reject")}
              >
                ✕ Reject
              </button>
            </div>

            {decision === "correct" && (
              <div style={{ marginTop: 14, border: "1px solid #ead9a8", background: "#fffaf0", borderRadius: 10, padding: 12 }}>
                <strong>Demo correction override</strong>
                <p className={`${styles.small} ${styles.muted}`}>These fields illustrate an analyst correction layer. They do not alter the adjudicated corpus or backend.</p>

                <label className={styles.small} htmlFor="corrected-summary"><strong>Corrected summary</strong></label>
                <textarea
                  id="corrected-summary"
                  value={correctedSummary}
                  onChange={(event) => setCorrectedSummary(event.target.value)}
                  style={{ width: "100%", minHeight: 82, marginTop: 6, border: "1px solid #dce6f0", borderRadius: 9, padding: 10, font: "inherit" }}
                />

                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 10, marginTop: 10 }}>
                  <label className={styles.small}>
                    <strong>Signal type</strong>
                    <input
                      value={correctedType}
                      onChange={(event) => setCorrectedType(event.target.value)}
                      style={{ width: "100%", marginTop: 6, border: "1px solid #dce6f0", borderRadius: 9, padding: 9, font: "inherit" }}
                    />
                  </label>
                  <label className={styles.small}>
                    <strong>Signal role</strong>
                    <input
                      value={correctedRole}
                      onChange={(event) => setCorrectedRole(event.target.value)}
                      style={{ width: "100%", marginTop: 6, border: "1px solid #dce6f0", borderRadius: 9, padding: 9, font: "inherit" }}
                    />
                  </label>
                </div>
              </div>
            )}

            <label className={styles.small} htmlFor="review-comment" style={{ display: "block", marginTop: 14 }}><strong>Analyst note</strong></label>
            <textarea
              id="review-comment"
              aria-label="Review comment"
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              placeholder="Optional rationale or clarification…"
              style={{ width: "100%", minHeight: 90, marginTop: 6, border: "1px solid #dce6f0", borderRadius: 9, padding: 10, font: "inherit" }}
            />

            <button
              disabled={!decision}
              className={`${styles.button} ${styles.buttonPrimary}`}
              style={{ marginTop: 10, opacity: decision ? 1 : 0.5 }}
              onClick={() => setSubmitted(true)}
            >
              Apply demo decision
            </button>
          </section>

          <section className={styles.card}>
            <h2>Downstream impact preview</h2>
            {!selectedDecision && (
              <div className={styles.detailPanel}>
                Select Confirm, Correct or Reject to preview how human review changes the intelligence workflow.
              </div>
            )}

            {selectedDecision && (
              <>
                <div className={styles.detailPanel}>
                  <strong>{selectedDecision.title}</strong><br />
                  {selectedDecision.summary}
                </div>
                <ol className={styles.insights}>
                  {selectedDecision.effects.map((effect) => <li key={effect}>{effect}</li>)}
                </ol>

                {decision === "correct" && (
                  <div style={{ background: "#f8fafc", border: "1px solid #dce6f0", borderRadius: 10, padding: 12, marginTop: 12 }}>
                    <div className={styles.small}><strong>Correction payload preview</strong></div>
                    <pre style={{ whiteSpace: "pre-wrap", overflow: "auto", marginBottom: 0, fontSize: 11, lineHeight: 1.5 }}>{JSON.stringify({
                      signal_id: signal.id,
                      summary: correctedSummary,
                      signal_type: correctedType,
                      signal_role: correctedRole,
                    }, null, 2)}</pre>
                  </div>
                )}
              </>
            )}

            {submitted && selectedDecision && (
              <div style={{ marginTop: 14, border: "1px solid #b9ddc4", background: "#f2fbf5", borderRadius: 10, padding: 12 }}>
                <strong>Demo review recorded locally</strong>
                <div className={styles.small} style={{ marginTop: 6 }}>Status: {selectedDecision.status}</div>
                <div className={styles.small}>Audit note: {comment.trim() || "No analyst note supplied"}</div>
                <div className={`${styles.small} ${styles.muted}`} style={{ marginTop: 6 }}>Production implementation would persist an immutable review record and trigger the appropriate downstream workflow.</div>
              </div>
            )}
          </section>
        </div>
      </div>
    </DemoShell>
  );
}
