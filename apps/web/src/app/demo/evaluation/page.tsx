import Link from "next/link";
import { DemoShell, PrototypeNote } from "../demo-shell";
import { mvHondiusBenchmark } from "../mv-hondius-data";
import { mvHondiusV044FullEvaluation as current } from "./mv-hondius-v044-full-summary";
import styles from "../demo.module.css";

const historicalPartial = {
  report: "evaluation/reports/mv-hondius-corpus-v041.json",
  coverage: "1/6",
  meanSignalF1: 1.0,
  meanEvidenceF1: 1.0,
  meanRoleAccuracy: 1.0,
  meanTypeAccuracy: 1.0,
  corpusComplete: false,
  metricsPass: true,
  eventMatcherReady: false,
} as const;

const thresholdRows = [
  ["Mean signal F1", current.aggregate.meanSignalF1, current.releaseGate.thresholds.meanSignalF1],
  ["Mean evidence support F1", current.aggregate.meanEvidenceSupportF1, current.releaseGate.thresholds.meanEvidenceSupportF1],
  ["Signal role accuracy", current.aggregate.meanSignalRoleAccuracy, current.releaseGate.thresholds.meanSignalRoleAccuracy],
  ["Signal type accuracy", current.aggregate.meanSignalTypeAccuracy, current.releaseGate.thresholds.meanSignalTypeAccuracy],
] as const;

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function SystemEvaluationPage() {
  const micro = current.aggregate.microSignalDetection;

  return (
    <DemoShell active="evaluation">
      <div className={styles.content}>
        <PrototypeNote>
          Full-corpus evaluation view — the primary values below come from a real local OETI evaluate-corpus run against all six adjudicated MV Hondius gold-standard documents using the manifest-versioned v0.4.4 prediction architecture. The detailed JSON remains in the local tmp output; this demo branch stores a faithful summary, not a replacement canonical backend report.
        </PrototypeNote>

        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">Threats</Link> › MV Hondius › System Evaluation</div>
        <div className={styles.pageHead}>
          <div>
            <h1>System Evaluation — MV Hondius full corpus</h1>
            <p className={styles.subtitle}>Case {current.caseCode} · Benchmark v{current.benchmarkVersion} · Architecture {current.predictionArchitecture}</p>
          </div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/threats/hantavirus">← Threat Explorer</Link></div>
        </div>

        <section className={styles.grid4}>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.green}`}>6</div>
            <div><span className={styles.metricValue}>6/6</span><div className={styles.metricLabel}>Documents evaluated</div><small className={styles.muted}>0 skipped · corpus complete</small></div>
          </article>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.orange}`}>F1</div>
            <div><span className={styles.metricValue}>{current.aggregate.meanSignalF1.toFixed(3)}</span><div className={styles.metricLabel}>Mean signal F1</div><small className={styles.muted}>Release threshold ≥ 0.90</small></div>
          </article>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.red}`}>E</div>
            <div><span className={styles.metricValue}>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</span><div className={styles.metricLabel}>Evidence support F1</div><small className={styles.muted}>Release threshold ≥ 0.90</small></div>
          </article>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.purple}`}>×</div>
            <div><span className={styles.metricValue}>Blocked</span><div className={styles.metricLabel}>Event matcher gate</div><small className={styles.muted}>Corpus complete, metrics below gate</small></div>
          </article>
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Release gate — full 6-document evaluation</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Corpus complete</div><div><span className={`${styles.pill} ${styles.pillReviewed}`}>Yes · 6/6</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Metrics pass</div><div><span className={`${styles.pill} ${styles.pillHigh}`}>No</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Event matcher ready</div><div><span className={`${styles.pill} ${styles.pillHigh}`}>No</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Signal-role accuracy</div><div>{pct(current.aggregate.meanSignalRoleAccuracy)}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Signal-type accuracy</div><div>{pct(current.aggregate.meanSignalTypeAccuracy)}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Evidence exact F1</div><div>{current.aggregate.meanEvidenceExactF1.toFixed(3)}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Evidence support F1</div><div>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</div></div>
            </div>
            <div className={styles.detailPanel}>
              <strong>Interpretation</strong><br />The corpus-coverage requirement is now satisfied, but the release gate remains closed because mean signal F1 and evidence-support F1 are below their configured thresholds. Perfect role/type classification does not compensate for over-detection and weak evidence matching.
            </div>
          </section>

          <section className={styles.card}>
            <h2>Micro signal detection — all documents combined</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10, marginTop: 12 }}>
              <div style={{ background: "#e8f8ec", color: "#123b22", borderRadius: 12, padding: 24, textAlign: "center" }}><div className={styles.metricValue}>{micro.tp}</div><strong>True positive</strong></div>
              <div style={{ background: "#fff3d5", color: "#6b4500", borderRadius: 12, padding: 24, textAlign: "center" }}><div className={styles.metricValue}>{micro.fp}</div><strong>False positive</strong></div>
              <div style={{ background: "#ffeaea", color: "#7f1d1d", borderRadius: 12, padding: 24, textAlign: "center" }}><div className={styles.metricValue}>{micro.fn}</div><strong>False negative</strong></div>
            </div>
            <div className={styles.summaryList} style={{ marginTop: 16 }}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Gold signals</div><div>{micro.goldSignals}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Predicted signals</div><div>{micro.predictedSignals}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Precision</div><div><strong>{micro.precision.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Recall</div><div><strong>{micro.recall.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Micro F1</div><div><strong>{micro.f1.toFixed(3)}</strong></div></div>
            </div>
            <div className={styles.detailPanel}><strong>Main error pattern</strong><br />Recall is high at 0.90, but precision falls to 0.659 because the system produced 14 false-positive signals. The current extractor/assembler is therefore finding most expected signals while also splitting or generating additional signals that the gold standard does not support.</div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Release thresholds vs. full-corpus result</h2>
            <table className={styles.table}>
              <thead><tr><th>Metric</th><th>Observed</th><th>Threshold</th><th>Status</th></tr></thead>
              <tbody>
                {thresholdRows.map(([label, observed, threshold]) => (
                  <tr key={label}>
                    <td>{label}</td><td><strong>{observed.toFixed(3)}</strong></td><td>≥ {threshold.toFixed(2)}</td>
                    <td><span className={`${styles.pill} ${observed >= threshold ? styles.pillReviewed : styles.pillHigh}`}>{observed >= threshold ? "Pass" : "Below threshold"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className={styles.detailPanel}><strong>Gate logic</strong><br />All four metric thresholds plus corpus completeness must pass simultaneously. In this run, role and type pass; mean signal F1 and evidence-support F1 do not.</div>
          </section>

          <section className={styles.card}>
            <h2>Evidence quality</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Exact evidence F1</div><div><strong>{current.aggregate.meanEvidenceExactF1.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Support-equivalent evidence F1</div><div><strong>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Release threshold</div><div>≥ {current.releaseGate.thresholds.meanEvidenceSupportF1.toFixed(2)}</div></div>
            </div>
            <ul className={styles.insights}>
              <li>Exact evidence matching is very low, meaning extracted support spans frequently differ from adjudicated evidence spans.</li>
              <li>Support-equivalent scoring improves the result, but 0.461 remains far below the 0.90 release threshold.</li>
              <li>This suggests that evidence binding and claim-to-signal support need improvement independently of signal role/type classification.</li>
            </ul>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>Signal detection by document</h2>
          <table className={styles.table}>
            <thead><tr><th>Document</th><th>TP</th><th>FP</th><th>FN</th><th>Signal F1</th></tr></thead>
            <tbody>
              {current.documents.map((doc) => (
                <tr key={doc.label}>
                  <td><strong>{doc.label}</strong></td><td>{doc.tp}</td><td>{doc.fp}</td><td>{doc.fn}</td><td><strong>{doc.f1.toFixed(3)}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Where the errors concentrate</h2>
            <ul className={styles.insights}>
              <li><strong>BEN SE18:</strong> 4 TP, 4 FP, 1 FN, F1 0.615 — the highest false-positive burden in the corpus.</li>
              <li><strong>Mendoza rodents:</strong> 3 TP, 2 FP, 1 FN, F1 0.667 — negative evidence and travel-history context remain challenging.</li>
              <li><strong>Initial notification:</strong> 6 TP, 3 FP, 1 FN, F1 0.750 — even the primary outbreak document is now less clean under the atomic-claims/assembly architecture than the earlier single-document historical run.</li>
              <li><strong>BEN SE17:</strong> 6 TP, 1 FP, 0 FN, F1 0.923 — strongest document-level signal detection in this six-document run.</li>
            </ul>
            <div className={styles.detailPanel}><strong>Development implication</strong><br />The next backend optimization should target deterministic assembly and evidence attachment: reduce redundant/over-split signals while preserving the current high recall and perfect role/type accuracy.</div>
          </section>

          <section className={styles.card}>
            <h2>Current vs. historical evaluation</h2>
            <table className={styles.table}>
              <thead><tr><th>Run</th><th>Coverage</th><th>Signal F1</th><th>Evidence F1</th><th>Metrics pass</th><th>Event matcher</th></tr></thead>
              <tbody>
                <tr><td><strong>Historical corpus runner v0.41</strong></td><td>{historicalPartial.coverage}</td><td>{historicalPartial.meanSignalF1.toFixed(3)}</td><td>{historicalPartial.meanEvidenceF1.toFixed(3)}</td><td>Yes on subset</td><td>No</td></tr>
                <tr><td><strong>Full corpus v0.4.4</strong></td><td>6/6</td><td>{current.aggregate.meanSignalF1.toFixed(3)}</td><td>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</td><td>No</td><td>No</td></tr>
              </tbody>
            </table>
            <div className={styles.detailPanel}><strong>Why the score fell</strong><br />The historical 1.00 result covered only the easiest single document. Full-corpus evaluation exposes harder transmission, genomic, wildlife, negative-evidence and mobility contexts. The lower score is therefore a more informative system measurement, not evidence that the evaluator regressed.</div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Benchmark configuration</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Case code</div><div>{current.caseCode}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Benchmark version</div><div>{current.benchmarkVersion}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Configured documents</div><div>{mvHondiusBenchmark.documentCount}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Prediction architecture</div><div style={{ overflowWrap: "anywhere" }}>{current.predictionArchitecture}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Matching model</div><div>Signal-level TP / FP / FN; no TN universe defined</div></div>
            </div>
          </section>

          <section className={styles.card}>
            <h2>Provenance</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Evaluation source</div><div>Real local evaluate-corpus run</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Detailed local output</div><div style={{ overflowWrap: "anywhere" }}>{current.provenance.sourceReport}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Demo representation</div><div>Versioned summary of reported aggregate and document-level signal metrics</div></div>
            </div>
            <div className={styles.detailPanel}>The branch intentionally does not pretend that the locally generated tmp JSON is already a canonical persisted backend report. Once the full report is deliberately versioned, this screen can read that artifact directly.</div>
          </section>
        </div>
      </div>
    </DemoShell>
  );
}
