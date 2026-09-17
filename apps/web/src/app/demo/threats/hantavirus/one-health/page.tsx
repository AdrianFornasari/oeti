import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../../demo-shell";
import styles from "../../../demo.module.css";

const months = [
  { month: "May", human: 0, animal: 3, environment: 0 },
  { month: "June", human: 0, animal: 2, environment: 1 },
  { month: "July", human: 1, animal: 1, environment: 2 },
  { month: "August", human: 1, animal: 1, environment: 0 },
  { month: "September", human: 0, animal: 0, environment: 0 },
];

export default function OneHealthConvergencePage() {
  return (
    <DemoShell active="threats">
      <div className={styles.content}>
        <PrototypeNote>Concept prototype — cross-domain convergence shown here is illustrative and intended to demonstrate the analytical view.</PrototypeNote>
        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">Threats</Link> › Hantavirus › One Health View</div>
        <div className={styles.pageHead}>
          <div><h1>Hantavirus — One Health Convergence</h1><p className={styles.subtitle}>Integrated view of human, animal and environmental signals.</p></div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/threats/hantavirus">← Threat Explorer</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/signals/asm-01">Open signal detail →</Link></div>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>Cross-domain convergence</h2>
            <div style={{ position: "relative", height: 360, display: "grid", placeItems: "center" }}>
              <div style={{ position: "absolute", width: 190, height: 190, borderRadius: "50%", background: "rgba(23,105,224,.18)", top: 28, left: "32%", display: "grid", placeItems: "start center", paddingTop: 28, fontWeight: 700 }}>Human<br /><span className={styles.small}>2 signals</span></div>
              <div style={{ position: "absolute", width: 190, height: 190, borderRadius: "50%", background: "rgba(22,163,74,.20)", bottom: 28, left: "19%", display: "grid", placeItems: "end center", paddingBottom: 26, fontWeight: 700 }}>Animal<br /><span className={styles.small}>7 signals</span></div>
              <div style={{ position: "absolute", width: 190, height: 190, borderRadius: "50%", background: "rgba(124,58,237,.18)", bottom: 28, right: "19%", display: "grid", placeItems: "end center", paddingBottom: 26, fontWeight: 700 }}>Environment<br /><span className={styles.small}>3 signals</span></div>
              <div style={{ position: "absolute", zIndex: 2, width: 110, height: 110, borderRadius: "50%", background: "#0d2b4b", color: "white", display: "grid", placeItems: "center", textAlign: "center", fontWeight: 800 }}>One Health<br />event</div>
            </div>
          </section>

          <section className={styles.card}>
            <h2>Signal distribution</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Human</div><div>2 signals</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Animal</div><div>7 signals</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Environment</div><div>3 signals</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Independent sources</div><div>5</div></div>
            </div>
            <h2 style={{ marginTop: 18 }}>Interpretation</h2>
            <ul className={styles.insights}>
              <li>Animal findings appear earliest in this demonstration sequence.</li>
              <li>Environmental findings add context to possible circulation.</li>
              <li>Human signals convert a reservoir-focused pattern into a cross-domain threat view.</li>
            </ul>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>Cross-domain timeline</h2>
          <table className={styles.table}>
            <thead><tr><th>Month</th><th>Human</th><th>Animal</th><th>Environment</th></tr></thead>
            <tbody>{months.map((row) => <tr key={row.month}><td><strong>{row.month}</strong></td><td>{"● ".repeat(row.human) || "—"}</td><td>{"● ".repeat(row.animal) || "—"}</td><td>{"● ".repeat(row.environment) || "—"}</td></tr>)}</tbody>
          </table>
        </section>
      </div>
    </DemoShell>
  );
}
