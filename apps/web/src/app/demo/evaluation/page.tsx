import Link from "next/link";
import { DemoShell, PrototypeNote } from "../demo-shell";
import { mvHondiusBenchmark } from "../mv-hondius-data";
import styles from "../demo.module.css";

const latestPersisted = {
  report: "evaluation/reports/mv-hondius-corpus-v041.json",
  evaluationSchemaVersion: "0.1",
  evaluatedDocuments: 1,
  skippedDocuments: 5,
  matchingThreshold: 0.55,
  signalDetection: {
    tp: 7,
    fp: 0,
    fn: 0,
    precision: 1.0,
    recall: 1.0,
    f1: 1.0,
    goldSignals: 7,
    predictedSignals: 7,
    matchedSignals: 7,
  },
  aggregate: {
    meanSignalF1: 1.0,
    meanEvidenceF1: 1.0,
    meanSignalRoleAccuracy: 1.0,
    meanSignalTypeAccuracy: 1.0,
  },
  fieldMetrics: [
    ["Signal role accuracy", 1.0],
    ["Signal type accuracy", 1.0],
    ["Disease accuracy", 1.0],
    ["Pathogen accuracy", 1.0],
    ["Normalization status accuracy", 1.0],
    ["Event date accuracy", 1.0],
    ["Reference period accuracy", 0.857143],
    ["Diagnostics accuracy", 0.857143],
    ["Domains F1", 1.0],
    ["Metrics F1", 1.0],
    ["Locations F1", 0.642857],
    ["Hosts F1", 0.857143],
    ["Evidence F1", 1.0],
  ] as const,
  compositeScore: 0.943878,
  releaseGate: {
    corpusComplete: false,
    metricsPass: true,
    eventMatcherReady: false,
    minimumDocuments: 6,
  },
} as const;

const historicalReports = [
  {
    name: "Single-document v0.35",
    path: "evaluation/reports/mv-hondius-2026-05-04-v035.json",
    coverage: "1 document",
    signalF1: 1.0,
    composite: 0.979592,
    locationsF1: 1.0,
    referencePeriod: 0.857143,
    diagnostics: 0.857143,
  },
  {
    name: "Corpus runner v0.41",
    path: latestPersisted.report,
    coverage: "1 evaluated / 6 configured",
    signalF1: 1.0,
    composite: latestPersisted.compositeScore,
    locationsF1: 0.642857,
    referencePeriod: 0.857143,
    diagnostics: 0.857143,
  },
] as const;

const thresholdRows = [
  ["Mean signal F1", latestPersisted.aggregate.meanSignalF1, mvHondiusBenchmark.releaseThresholds.meanSignalF1],
  ["Mean evidence F1", latestPersisted.aggregate.meanEvidenceF1, mvHondiusBenchmark.releaseThresholds.meanEvidenceSupportF1],
  ["Signal role accuracy", latestPersisted.aggregate.meanSignalRoleAccuracy, mvHondiusBenchmark.releaseThresholds.meanSignalRoleAccuracy],
  ["Signal type accuracy", latestPersisted.aggregate.meanSignalTypeAccuracy, mvHondiusBenchmark.releaseThresholds.meanSignalTypeAccuracy],
] as const;

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function SystemEvaluationPage() {
  return (
    <DemoShell active="evaluation">
      <div className={styles.content}>
        <PrototypeNote>
          Grounded evaluation view — values below come from persisted OETI evaluation reports and the current MV Hondius benchmark manifest. The latest persisted corpus report evaluated only 1 of 6 documents, so it must not be interpreted as full-corpus performance.
        </PrototypeNote>

        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">Threats</Link> › MV Hondius › System Evaluation</div>
        <div className={styles.pageHead}>
          <div>
            <h1>System Evaluation — MV Hondius benchmark</h1>
            <p className={styles.subtitle}>Case {mvHondiusBenchmark.caseCode} · Benchmark v{mvHondiusBenchmark.benchmarkVersion} · Evaluation schema v{latestPersisted.evaluationSchemaVersion}</p>
          </div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/threats/hantavirus">← Threat Explorer</Link></div>
        </div>

        <section className={styles.grid4}>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.blue}`}>6</div>
            <div><span className={styles.metricValue}>6/6</span><div className={styles.metricLabel}>Gold documents adjudicated now</div><small className={styles.muted}>Current benchmark manifest</small></div>
          </article>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.orange}`}>1</div>
            <div><span className={styles.metricValue}>1/6</span><div className={styles.metricLabel}>Documents in latest persisted evaluation</div><small className={styles.muted}>5 were skipped at report time</small></div>
          </article>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.green}`}>F1</div>
            <div><span className={styles.metricValue}>1.00</span><div className={styles.metricLabel}>Signal detection F1</div><small className={styles.muted}>Observed on the one evaluated document</small></div>
          </article>
          <article className={`${styles.card} ${styles.metric}`}>
            <div className={`${styles.metricIcon} ${styles.purple}`}>Σ</div>
            <div><span className={styles.metricValue}>0.944</span><div className={styles.metricLabel}>Composite score</div><small className={styles.muted}>Initial notification only</small></div>
          </article>
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Release gate — latest persisted report</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Metrics threshold gate</div><div><span className={`${styles.pill} ${styles.pillReviewed}`}>Pass on evaluated subset</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Corpus complete</div><div><span className={`${styles.pill} ${styles.pillMedium}`}>No in v0.41 report</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Evaluated documents</div><div>{latestPersisted.evaluatedDocuments} of {latestPersisted.releaseGate.minimumDocuments}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Event matcher ready</div><div><span className={`${styles.pill} ${styles.pillMedium}`}>No</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Current gold corpus</div><div>6 of 6 documents are now adjudicated</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Next required action</div><div>Run and persist a new full-corpus evaluation using all six adjudicated documents.</div></div>
            </div>
            <div className={styles.detailPanel}>
              <strong>Interpretation</strong><br />The 100% signal-detection result is valid for the evaluated initial-notification document, but it is not evidence that the six-document corpus has 100% performance. The persisted release gate correctly remained closed because corpus coverage was incomplete.
            </div>
          </section>

          <section className={styles.card}>
            <h2>Signal matching — evaluated document</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10, marginTop: 12 }}>
              <div style={{ background: "#e8f8ec", color: "#123b22", borderRadius: 12, padding: 24, textAlign: "center" }}><div className={styles.metricValue}>{latestPersisted.signalDetection.tp}</div><strong>True positive</strong></div>
              <div style={{ background: "#fff3d5", color: "#6b4500", borderRadius: 12, padding: 24, textAlign: "center" }}><div className={styles.metricValue}>{latestPersisted.signalDetection.fp}</div><strong>False positive</strong></div>
              <div style={{ background: "#ffeaea", color: "#7f1d1d", borderRadius: 12, padding: 24, textAlign: "center" }}><div className={styles.metricValue}>{latestPersisted.signalDetection.fn}</div><strong>False negative</strong></div>
            </div>
            <div className={styles.summaryList} style={{ marginTop: 16 }}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Gold signals</div><div>{latestPersisted.signalDetection.goldSignals}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Predicted signals</div><div>{latestPersisted.signalDetection.predictedSignals}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Matched signals</div><div>{latestPersisted.signalDetection.matchedSignals}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Matching threshold</div><div>{latestPersisted.matchingThreshold}</div></div>
            </div>
            <div className={styles.detailPanel}><strong>No True Negative cell</strong><br />OETI does not define a closed universe of “all possible non-signals” in this benchmark, so a conventional TN count would be misleading and is intentionally omitted.</div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Release thresholds vs. persisted subset result</h2>
            <table className={styles.table}>
              <thead><tr><th>Metric</th><th>Observed</th><th>Release threshold</th><th>Subset status</th></tr></thead>
              <tbody>
                {thresholdRows.map(([label, observed, threshold]) => (
                  <tr key={label}>
                    <td>{label}</td><td><strong>{observed.toFixed(2)}</strong></td><td>≥ {threshold.toFixed(2)}</td>
                    <td><span className={`${styles.pill} ${observed >= threshold ? styles.pillReviewed : styles.pillHigh}`}>{observed >= threshold ? "Pass" : "Below threshold"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className={styles.detailPanel}><strong>Important</strong><br />Passing these thresholds on one document does not open the overall release gate. Corpus completeness is a separate requirement.</div>
          </section>

          <section className={styles.card}>
            <h2>Field-level performance — persisted v0.41</h2>
            <table className={styles.table}>
              <thead><tr><th>Field</th><th>Score</th></tr></thead>
              <tbody>{latestPersisted.fieldMetrics.map(([field, score]) => <tr key={field}><td>{field}</td><td><strong>{pct(score)}</strong></td></tr>)}</tbody>
            </table>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>What the persisted report actually tells us</h2>
            <ul className={styles.insights}>
              <li>All 7 gold signals in the 04 May initial-notification document were matched: TP 7, FP 0, FN 0.</li>
              <li>Signal role, signal type, disease, pathogen, domains, metrics and evidence scored 1.0 on that document.</li>
              <li>The weakest reported field was location matching at 0.642857; reference-period, diagnostics and host metrics were each 0.857143.</li>
              <li>The aggregate metrics passed their configured thresholds, but five documents were skipped because their gold standards had not yet been adjudicated when v0.41 was generated.</li>
              <li>The gold standards are now adjudicated for all six configured documents, so the next meaningful measurement is a new full-corpus evaluation—not extrapolation from the one-document result.</li>
            </ul>
          </section>

          <section className={styles.card}>
            <h2>Benchmark configuration</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Case code</div><div>{mvHondiusBenchmark.caseCode}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Benchmark version</div><div>{mvHondiusBenchmark.benchmarkVersion}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Configured documents</div><div>{mvHondiusBenchmark.documentCount}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Prediction architecture</div><div style={{ overflowWrap: "anywhere" }}>{mvHondiusBenchmark.architecture}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Persisted report</div><div style={{ overflowWrap: "anywhere" }}>{latestPersisted.report}</div></div>
            </div>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>Persisted evaluation history</h2>
          <table className={styles.table}>
            <thead><tr><th>Report</th><th>Coverage</th><th>Signal F1</th><th>Composite</th><th>Locations F1</th><th>Reference period</th><th>Diagnostics</th></tr></thead>
            <tbody>
              {historicalReports.map((run) => (
                <tr key={run.name}>
                  <td><strong>{run.name}</strong><div className={`${styles.small} ${styles.muted}`}>{run.path}</div></td>
                  <td>{run.coverage}</td><td>{run.signalF1.toFixed(2)}</td><td>{run.composite.toFixed(3)}</td><td>{run.locationsF1.toFixed(3)}</td><td>{run.referencePeriod.toFixed(3)}</td><td>{run.diagnostics.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </DemoShell>
  );
}
