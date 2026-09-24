"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "../demo-shell";
import { useDemoPreferences } from "../demo-preferences";
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

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

const documentLabelsEs: Record<string, string> = {
  "Initial notification and national monitoring — 04 May 2026": "Notificación inicial y monitoreo nacional — 04 may 2026",
  "BEN SE17 — 12 May 2026": "BEN SE17 — 12 may 2026",
  "BEN SE18 — 19 May 2026": "BEN SE18 — 19 may 2026",
  "BEN SE19 — 26 May 2026": "BEN SE19 — 26 may 2026",
  "Tierra del Fuego rodents — 29 Jun 2026": "Roedores Tierra del Fuego — 29 jun 2026",
  "Mendoza rodents — 08 Jul 2026": "Roedores Mendoza — 08 jul 2026",
};

export default function SystemEvaluationPage() {
  const { isSpanish } = useDemoPreferences();
  const micro = current.aggregate.microSignalDetection;
  const documentLabel = (label: string) => isSpanish ? (documentLabelsEs[label] ?? label) : label;

  const thresholdRows = [
    [isSpanish ? "F1 medio de señales" : "Mean signal F1", current.aggregate.meanSignalF1, current.releaseGate.thresholds.meanSignalF1],
    [isSpanish ? "F1 medio de soporte de evidencia" : "Mean evidence support F1", current.aggregate.meanEvidenceSupportF1, current.releaseGate.thresholds.meanEvidenceSupportF1],
    [isSpanish ? "Exactitud del rol de señal" : "Signal role accuracy", current.aggregate.meanSignalRoleAccuracy, current.releaseGate.thresholds.meanSignalRoleAccuracy],
    [isSpanish ? "Exactitud del tipo de señal" : "Signal type accuracy", current.aggregate.meanSignalTypeAccuracy, current.releaseGate.thresholds.meanSignalTypeAccuracy],
  ] as const;

  return (
    <DemoShell active="evaluation">
      <div className={styles.content}>
        <PrototypeNote>{isSpanish
          ? "Vista de evaluación del corpus completo — los valores principales provienen de una corrida real local de OETI evaluate-corpus contra los seis documentos adjudicados del gold standard MV Hondius usando la arquitectura de predicción v0.4.4. El JSON detallado permanece en la salida local tmp; esta rama demo conserva un resumen fiel, no un reporte backend canónico sustituto."
          : "Full-corpus evaluation view — the primary values below come from a real local OETI evaluate-corpus run against all six adjudicated MV Hondius gold-standard documents using the manifest-versioned v0.4.4 prediction architecture. The detailed JSON remains in the local tmp output; this demo branch stores a faithful summary, not a replacement canonical backend report."}
        </PrototypeNote>

        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">{isSpanish ? "Amenazas" : "Threats"}</Link> › MV Hondius › {isSpanish ? "Evaluación del sistema" : "System Evaluation"}</div>
        <div className={styles.pageHead}>
          <div>
            <h1>{isSpanish ? "Evaluación del sistema — corpus completo MV Hondius" : "System Evaluation — MV Hondius full corpus"}</h1>
            <p className={styles.subtitle}>{isSpanish ? `Caso ${current.caseCode} · Benchmark v${current.benchmarkVersion} · Arquitectura ${current.predictionArchitecture}` : `Case ${current.caseCode} · Benchmark v${current.benchmarkVersion} · Architecture ${current.predictionArchitecture}`}</p>
          </div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/threats/hantavirus">← {isSpanish ? "Explorador de amenazas" : "Threat Explorer"}</Link></div>
        </div>

        <section className={styles.grid4}>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.green}`}>6</div><div><span className={styles.metricValue}>6/6</span><div className={styles.metricLabel}>{isSpanish ? "Documentos evaluados" : "Documents evaluated"}</div><small className={styles.muted}>{isSpanish ? "0 omitidos · corpus completo" : "0 skipped · corpus complete"}</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.orange}`}>F1</div><div><span className={styles.metricValue}>{current.aggregate.meanSignalF1.toFixed(3)}</span><div className={styles.metricLabel}>{isSpanish ? "F1 medio de señales" : "Mean signal F1"}</div><small className={styles.muted}>{isSpanish ? "Umbral de release ≥ 0.90" : "Release threshold ≥ 0.90"}</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.red}`}>E</div><div><span className={styles.metricValue}>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</span><div className={styles.metricLabel}>{isSpanish ? "F1 de soporte de evidencia" : "Evidence support F1"}</div><small className={styles.muted}>{isSpanish ? "Umbral de release ≥ 0.90" : "Release threshold ≥ 0.90"}</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.purple}`}>×</div><div><span className={styles.metricValue}>{isSpanish ? "Bloqueado" : "Blocked"}</span><div className={styles.metricLabel}>{isSpanish ? "Gate del event matcher" : "Event matcher gate"}</div><small className={styles.muted}>{isSpanish ? "Corpus completo, métricas bajo el gate" : "Corpus complete, metrics below gate"}</small></div></article>
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Gate de release — evaluación completa de 6 documentos" : "Release gate — full 6-document evaluation"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Corpus completo" : "Corpus complete"}</div><div><span className={`${styles.pill} ${styles.pillReviewed}`}>{isSpanish ? "Sí · 6/6" : "Yes · 6/6"}</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Métricas aprobadas" : "Metrics pass"}</div><div><span className={`${styles.pill} ${styles.pillHigh}`}>No</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Event matcher listo" : "Event matcher ready"}</div><div><span className={`${styles.pill} ${styles.pillHigh}`}>No</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Exactitud de rol" : "Signal-role accuracy"}</div><div>{pct(current.aggregate.meanSignalRoleAccuracy)}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Exactitud de tipo" : "Signal-type accuracy"}</div><div>{pct(current.aggregate.meanSignalTypeAccuracy)}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "F1 exacto de evidencia" : "Evidence exact F1"}</div><div>{current.aggregate.meanEvidenceExactF1.toFixed(3)}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "F1 de soporte de evidencia" : "Evidence support F1"}</div><div>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</div></div>
            </div>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Interpretación" : "Interpretation"}</strong><br />{isSpanish ? "El requisito de cobertura del corpus ya se cumple, pero el gate de release permanece cerrado porque el F1 medio de señales y el F1 de soporte de evidencia están por debajo de sus umbrales. Una clasificación perfecta de rol/tipo no compensa la sobredetección ni el matching débil de evidencia." : "The corpus-coverage requirement is now satisfied, but the release gate remains closed because mean signal F1 and evidence-support F1 are below their configured thresholds. Perfect role/type classification does not compensate for over-detection and weak evidence matching."}</div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Detección micro de señales — todos los documentos combinados" : "Micro signal detection — all documents combined"}</h2>
            <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10,marginTop:12}}>
              <div style={{background:"#e8f8ec",color:"#123b22",borderRadius:12,padding:24,textAlign:"center"}}><div className={styles.metricValue}>{micro.tp}</div><strong>{isSpanish ? "Verdadero positivo" : "True positive"}</strong></div>
              <div style={{background:"#fff3d5",color:"#6b4500",borderRadius:12,padding:24,textAlign:"center"}}><div className={styles.metricValue}>{micro.fp}</div><strong>{isSpanish ? "Falso positivo" : "False positive"}</strong></div>
              <div style={{background:"#ffeaea",color:"#7f1d1d",borderRadius:12,padding:24,textAlign:"center"}}><div className={styles.metricValue}>{micro.fn}</div><strong>{isSpanish ? "Falso negativo" : "False negative"}</strong></div>
            </div>
            <div className={styles.summaryList} style={{marginTop:16}}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Señales gold" : "Gold signals"}</div><div>{micro.goldSignals}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Señales predichas" : "Predicted signals"}</div><div>{micro.predictedSignals}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Precisión" : "Precision"}</div><div><strong>{micro.precision.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Recall</div><div><strong>{micro.recall.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Micro F1</div><div><strong>{micro.f1.toFixed(3)}</strong></div></div>
            </div>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Patrón principal de error" : "Main error pattern"}</strong><br />{isSpanish ? "El recall es alto (0.90), pero la precisión cae a 0.659 porque el sistema produjo 14 señales falsas positivas. El extractor/ensamblador actual encuentra la mayoría de las señales esperadas, pero también divide o genera señales adicionales que el gold standard no respalda." : "Recall is high at 0.90, but precision falls to 0.659 because the system produced 14 false-positive signals. The current extractor/assembler is therefore finding most expected signals while also splitting or generating additional signals that the gold standard does not support."}</div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Umbrales de release vs. resultado del corpus completo" : "Release thresholds vs. full-corpus result"}</h2>
            <table className={styles.table}><thead><tr><th>{isSpanish ? "Métrica" : "Metric"}</th><th>{isSpanish ? "Observado" : "Observed"}</th><th>{isSpanish ? "Umbral" : "Threshold"}</th><th>{isSpanish ? "Estado" : "Status"}</th></tr></thead><tbody>{thresholdRows.map(([label,observed,threshold]) => <tr key={label}><td>{label}</td><td><strong>{observed.toFixed(3)}</strong></td><td>≥ {threshold.toFixed(2)}</td><td><span className={`${styles.pill} ${observed>=threshold?styles.pillReviewed:styles.pillHigh}`}>{observed>=threshold?(isSpanish?"Aprueba":"Pass"):(isSpanish?"Bajo umbral":"Below threshold")}</span></td></tr>)}</tbody></table>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Lógica del gate" : "Gate logic"}</strong><br />{isSpanish ? "Los cuatro umbrales métricos y la completitud del corpus deben aprobar simultáneamente. En esta corrida, rol y tipo aprueban; F1 medio de señales y F1 de soporte de evidencia no." : "All four metric thresholds plus corpus completeness must pass simultaneously. In this run, role and type pass; mean signal F1 and evidence-support F1 do not."}</div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Calidad de evidencia" : "Evidence quality"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "F1 exacto de evidencia" : "Exact evidence F1"}</div><div><strong>{current.aggregate.meanEvidenceExactF1.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "F1 de evidencia equivalente en soporte" : "Support-equivalent evidence F1"}</div><div><strong>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Umbral de release" : "Release threshold"}</div><div>≥ {current.releaseGate.thresholds.meanEvidenceSupportF1.toFixed(2)}</div></div>
            </div>
            <ul className={styles.insights}><li>{isSpanish ? "El matching exacto de evidencia es muy bajo: los spans extraídos difieren con frecuencia de los spans adjudicados." : "Exact evidence matching is very low, meaning extracted support spans frequently differ from adjudicated evidence spans."}</li><li>{isSpanish ? "El scoring equivalente en soporte mejora el resultado, pero 0.461 sigue muy por debajo del umbral 0.90." : "Support-equivalent scoring improves the result, but 0.461 remains far below the 0.90 release threshold."}</li><li>{isSpanish ? "Esto sugiere que el binding evidencia-claim-señal necesita mejorar independientemente de la clasificación de rol/tipo." : "This suggests that evidence binding and claim-to-signal support need improvement independently of signal role/type classification."}</li></ul>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>{isSpanish ? "Detección de señales por documento" : "Signal detection by document"}</h2>
          <table className={styles.table}><thead><tr><th>{isSpanish ? "Documento" : "Document"}</th><th>TP</th><th>FP</th><th>FN</th><th>Signal F1</th></tr></thead><tbody>{current.documents.map((doc) => <tr key={doc.label}><td><strong>{documentLabel(doc.label)}</strong></td><td>{doc.tp}</td><td>{doc.fp}</td><td>{doc.fn}</td><td><strong>{doc.f1.toFixed(3)}</strong></td></tr>)}</tbody></table>
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Dónde se concentran los errores" : "Where the errors concentrate"}</h2>
            <ul className={styles.insights}>
              <li><strong>BEN SE18:</strong> {isSpanish ? "4 TP, 4 FP, 1 FN, F1 0.615 — la mayor carga de falsos positivos del corpus." : "4 TP, 4 FP, 1 FN, F1 0.615 — the highest false-positive burden in the corpus."}</li>
              <li><strong>{isSpanish ? "Roedores Mendoza" : "Mendoza rodents"}:</strong> {isSpanish ? "3 TP, 2 FP, 1 FN, F1 0.667 — la evidencia negativa y el contexto de viaje siguen siendo difíciles." : "3 TP, 2 FP, 1 FN, F1 0.667 — negative evidence and travel-history context remain challenging."}</li>
              <li><strong>{isSpanish ? "Notificación inicial" : "Initial notification"}:</strong> 6 TP, 3 FP, 1 FN, F1 0.750.</li>
              <li><strong>BEN SE17:</strong> {isSpanish ? "6 TP, 1 FP, 0 FN, F1 0.923 — mejor detección a nivel documento." : "6 TP, 1 FP, 0 FN, F1 0.923 — strongest document-level signal detection."}</li>
            </ul>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Implicancia de desarrollo" : "Development implication"}</strong><br />{isSpanish ? "La próxima optimización backend debería apuntar al ensamblado determinístico y al attachment de evidencia: reducir señales redundantes o sobredesagregadas preservando el recall alto y la exactitud perfecta de rol/tipo." : "The next backend optimization should target deterministic assembly and evidence attachment: reduce redundant/over-split signals while preserving the current high recall and perfect role/type accuracy."}</div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Evaluación actual vs. histórica" : "Current vs. historical evaluation"}</h2>
            <table className={styles.table}><thead><tr><th>{isSpanish ? "Corrida" : "Run"}</th><th>{isSpanish ? "Cobertura" : "Coverage"}</th><th>Signal F1</th><th>Evidence F1</th><th>{isSpanish ? "Métricas" : "Metrics pass"}</th><th>Event matcher</th></tr></thead><tbody><tr><td><strong>Historical corpus runner v0.41</strong></td><td>{historicalPartial.coverage}</td><td>{historicalPartial.meanSignalF1.toFixed(3)}</td><td>{historicalPartial.meanEvidenceF1.toFixed(3)}</td><td>{isSpanish ? "Sí en subset" : "Yes on subset"}</td><td>No</td></tr><tr><td><strong>Full corpus v0.4.4</strong></td><td>6/6</td><td>{current.aggregate.meanSignalF1.toFixed(3)}</td><td>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</td><td>No</td><td>No</td></tr></tbody></table>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Por qué bajó el score" : "Why the score fell"}</strong><br />{isSpanish ? "El resultado histórico 1.00 cubría solo el documento más sencillo. La evaluación completa expone contextos más difíciles de transmisión, genómica, fauna, evidencia negativa y movilidad. El score menor es una medición más informativa del sistema, no prueba de que el evaluador haya regresado." : "The historical 1.00 result covered only the easiest single document. Full-corpus evaluation exposes harder transmission, genomic, wildlife, negative-evidence and mobility contexts. The lower score is therefore a more informative system measurement, not evidence that the evaluator regressed."}</div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}><h2>{isSpanish ? "Configuración del benchmark" : "Benchmark configuration"}</h2><div className={styles.summaryList}>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Código de caso" : "Case code"}</div><div>{current.caseCode}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Versión benchmark" : "Benchmark version"}</div><div>{current.benchmarkVersion}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Documentos configurados" : "Configured documents"}</div><div>{mvHondiusBenchmark.documentCount}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Arquitectura de predicción" : "Prediction architecture"}</div><div style={{overflowWrap:"anywhere"}}>{current.predictionArchitecture}</div></div>
          </div></section>
          <section className={styles.card}><h2>{isSpanish ? "Procedencia" : "Provenance"}</h2><div className={styles.summaryList}>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Fuente de evaluación" : "Evaluation source"}</div><div>{isSpanish ? "Corrida local real de evaluate-corpus" : "Real local evaluate-corpus run"}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Salida local detallada" : "Detailed local output"}</div><div style={{overflowWrap:"anywhere"}}>{current.provenance.sourceReport}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Representación demo" : "Demo representation"}</div><div>{isSpanish ? "Resumen versionado de métricas agregadas y por documento" : "Versioned summary of reported aggregate and document-level signal metrics"}</div></div>
          </div></section>
        </div>
      </div>
    </DemoShell>
  );
}