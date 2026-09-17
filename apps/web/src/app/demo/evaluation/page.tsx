import { DemoShell, PrototypeNote } from "../demo-shell";
import styles from "../demo.module.css";

const runs = [
  ["16 Sep 2026 10:24", "MV Hondius (v1.0)", "124", "0.87", "0.82", "0.84", "Completed"],
  ["02 Sep 2026 14:11", "MV Hondius (v0.9)", "118", "0.83", "0.78", "0.80", "Completed"],
  ["18 Aug 2026 09:37", "MV Hondius (v0.8)", "102", "0.81", "0.74", "0.77", "Completed"],
];

export default function SystemEvaluationPage() {
  return (
    <DemoShell active="evaluation">
      <div className={styles.content}>
        <PrototypeNote>Concept prototype — metrics below illustrate the intended evaluation interface and are not claims of real-world OETI performance.</PrototypeNote>
        <div className={styles.breadcrumb}>Evaluation › System Evaluation</div>
        <div className={styles.pageHead}>
          <div><h1>System Evaluation</h1><p className={styles.subtitle}>Monitor system performance in detecting and characterizing emerging threats.</p></div>
          <div className={styles.actions}><button className={`${styles.button} ${styles.buttonPrimary}`}>Export report</button></div>
        </div>

        <section className={styles.grid4}>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.blue}`}>◎</div><div><span className={styles.metricValue}>0.87</span><div className={styles.metricLabel}>Precision</div><small className={styles.muted}>Correct positive signals</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.green}`}>⌘</div><div><span className={styles.metricValue}>0.82</span><div className={styles.metricLabel}>Recall</div><small className={styles.muted}>Detected true signals</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.purple}`}>▥</div><div><span className={styles.metricValue}>0.84</span><div className={styles.metricLabel}>F1 Score</div><small className={styles.muted}>Overall performance</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.red}`}>◷</div><div><span className={styles.metricValue}>2.3 d</span><div className={styles.metricLabel}>Median time to detect</div><small className={styles.muted}>From first source to signal</small></div></article>
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Performance over time</h2>
            <div style={{ height: 260, display: "grid", placeItems: "center", background: "linear-gradient(180deg,#f8fbff,#eef5fb)", borderRadius: 12, border: "1px solid #dce6f0" }}>
              <svg width="92%" height="210" viewBox="0 0 760 210" role="img" aria-label="Illustrative performance trend chart">
                {[40,80,120,160].map((y) => <line key={y} x1="50" y1={y} x2="730" y2={y} stroke="#dbe6f0" strokeWidth="1" />)}
                <polyline points="60,150 190,130 320,110 450,98 580,88 710,70" fill="none" stroke="#1769e0" strokeWidth="4" />
                <polyline points="60,132 190,104 320,86 450,74 580,66 710,52" fill="none" stroke="#16a34a" strokeWidth="4" />
                <polyline points="60,142 190,118 320,98 450,86 580,77 710,61" fill="none" stroke="#7c3aed" strokeWidth="4" />
              </svg>
            </div>
          </section>
          <section className={styles.card}>
            <h2>Confusion matrix (signals)</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 10, marginTop: 22 }}>
              <div style={{ background: "#e8f8ec", borderRadius: 12, padding: 28, textAlign: "center" }}><div className={styles.metricValue}>124</div><strong>True Positive</strong></div>
              <div style={{ background: "#ffeaea", borderRadius: 12, padding: 28, textAlign: "center" }}><div className={styles.metricValue}>27</div><strong>False Negative</strong></div>
              <div style={{ background: "#ffeaea", borderRadius: 12, padding: 28, textAlign: "center" }}><div className={styles.metricValue}>18</div><strong>False Positive</strong></div>
              <div style={{ background: "#e8f8ec", borderRadius: 12, padding: 28, textAlign: "center" }}><div className={styles.metricValue}>312</div><strong>True Negative</strong></div>
            </div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Performance by One Health domain</h2>
            <table className={styles.table}><thead><tr><th>Domain</th><th>Precision</th><th>Recall</th><th>F1</th><th>Signals</th></tr></thead><tbody>
              <tr><td>Human</td><td>0.89</td><td>0.81</td><td>0.85</td><td>48</td></tr>
              <tr><td>Animal</td><td>0.83</td><td>0.86</td><td>0.84</td><td>67</td></tr>
              <tr><td>Environment</td><td>0.79</td><td>0.76</td><td>0.77</td><td>32</td></tr>
              <tr><td>Cross-domain</td><td>0.88</td><td>0.82</td><td>0.85</td><td>21</td></tr>
            </tbody></table>
          </section>
          <section className={styles.card}>
            <h2>Gold standard</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Dataset</div><div>MV Hondius Evaluation Corpus</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Validated signals</div><div>124</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Period</div><div>May–September 2026</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Sources</div><div>28 documents</div></div>
            </div>
            <div className={styles.detailPanel}>Evaluation results shown in this sponsor demo are illustrative. Production screens will read from persisted evaluation runs generated by the backend.</div>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>Recent evaluation runs</h2>
          <table className={styles.table}><thead><tr><th>Date</th><th>Dataset</th><th>Signals</th><th>Precision</th><th>Recall</th><th>F1</th><th>Status</th></tr></thead><tbody>{runs.map((run) => <tr key={run[0]}>{run.map((cell, index) => <td key={`${run[0]}-${index}`}>{cell}</td>)}</tr>)}</tbody></table>
        </section>
      </div>
    </DemoShell>
  );
}
