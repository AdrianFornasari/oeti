"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "../demo-shell";
import { useDemoPreferences } from "../demo-preferences";
import { mvHondiusBenchmark } from "../mv-hondius-data";
import { mvHondiusV044FullEvaluation as current } from "./mv-hondius-v044-full-summary";
import styles from "../demo.module.css";

const historicalPartial = {
  coverage: "1/6",
  meanSignalF1: 1.0,
  meanEvidenceF1: 1.0,
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
    [isSpanish ? "F1 de soporte de evidencia" : "Evidence support F1", current.aggregate.meanEvidenceSupportF1, current.releaseGate.thresholds.meanEvidenceSupportF1],
    [isSpanish ? "Exactitud del rol de señal" : "Signal role accuracy", current.aggregate.meanSignalRoleAccuracy, current.releaseGate.thresholds.meanSignalRoleAccuracy],
    [isSpanish ? "Exactitud del tipo de señal" : "Signal type accuracy", current.aggregate.meanSignalTypeAccuracy, current.releaseGate.thresholds.meanSignalTypeAccuracy],
  ] as const;

  return (
    <DemoShell active="evaluation">
      <div className={styles.content}>
        <PrototypeNote>{isSpanish
          ? "Evaluación técnica real del caso MV Hondius — los valores provienen de una corrida de OETI contra los seis documentos adjudicados del corpus. Esta pantalla evalúa el desempeño del sistema, no la gravedad epidemiológica del evento."
          : "Real technical evaluation of the MV Hondius case — values come from an OETI run against all six adjudicated corpus documents. This screen evaluates system performance, not epidemiological severity."}
        </PrototypeNote>

        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">{isSpanish ? "Amenazas" : "Threats"}</Link> › MV Hondius › {isSpanish ? "Evaluación del sistema" : "System Evaluation"}</div>

        <div className={styles.pageHead}>
          <div>
            <h1>{isSpanish ? "Evaluación del sistema — corpus completo MV Hondius" : "System Evaluation — MV Hondius full corpus"}</h1>
            <p className={styles.subtitle}>{isSpanish ? `Caso ${current.caseCode} · Benchmark v${current.benchmarkVersion} · Arquitectura ${current.predictionArchitecture}` : `Case ${current.caseCode} · Benchmark v${current.benchmarkVersion} · Architecture ${current.predictionArchitecture}`}</p>
          </div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/threats/hantavirus">← {isSpanish ? "Explorador de amenazas" : "Threat Explorer"}</Link></div>
        </div>

        <section className={styles.card} style={{ marginBottom: 14 }}>
          <h2>{isSpanish ? "Lectura ejecutiva" : "Executive interpretation"}</h2>
          <div className={styles.summaryList}>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Cobertura" : "Coverage"}</div><div><strong>{isSpanish ? "Completa: 6 de 6 documentos" : "Complete: 6 of 6 documents"}</strong></div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Fortaleza actual" : "Current strength"}</div><div>{isSpanish ? "El sistema encuentra la mayoría de las señales esperadas y clasifica correctamente su tipo y rol." : "The system finds most expected signals and correctly classifies their type and role."}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Debilidad principal" : "Main weakness"}</div><div>{isSpanish ? "Genera señales adicionales no respaldadas por el gold standard y todavía vincula la evidencia textual con precisión insuficiente." : "It generates additional signals not supported by the gold standard and still links textual evidence with insufficient precision."}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Decisión técnica" : "Technical decision"}</div><div><strong>{isSpanish ? "No habilitar todavía el vinculador de eventos" : "Do not enable the event matcher yet"}</strong></div></div>
          </div>
        </section>

        <section className={styles.grid4}>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.green}`}>6</div><div><span className={styles.metricValue}>6/6</span><div className={styles.metricLabel}>{isSpanish ? "Documentos evaluados" : "Documents evaluated"}</div><small className={styles.muted}>{isSpanish ? "Corpus completo" : "Full corpus"}</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.orange}`}>F1</div><div><span className={styles.metricValue}>{current.aggregate.meanSignalF1.toFixed(3)}</span><div className={styles.metricLabel}>{isSpanish ? "F1 medio de señales" : "Mean signal F1"}</div><small className={styles.muted}>{isSpanish ? "Objetivo ≥ 0.90" : "Target ≥ 0.90"}</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.red}`}>E</div><div><span className={styles.metricValue}>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</span><div className={styles.metricLabel}>{isSpanish ? "Soporte de evidencia" : "Evidence support"}</div><small className={styles.muted}>{isSpanish ? "Objetivo ≥ 0.90" : "Target ≥ 0.90"}</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.purple}`}>×</div><div><span className={styles.metricValue}>{isSpanish ? "No" : "No"}</span><div className={styles.metricLabel}>{isSpanish ? "Vinculador de eventos habilitado" : "Event matcher enabled"}</div><small className={styles.muted}>{isSpanish ? "Criterios aún no cumplidos" : "Criteria not yet met"}</small></div></article>
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Criterios de habilitación" : "Release criteria"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Corpus completo" : "Corpus complete"}</div><div><span className={`${styles.pill} ${styles.pillReviewed}`}>{isSpanish ? "Sí · 6/6" : "Yes · 6/6"}</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Métricas aprobadas" : "Metrics pass"}</div><div><span className={`${styles.pill} ${styles.pillHigh}`}>No</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Vinculador de eventos listo" : "Event matcher ready"}</div><div><span className={`${styles.pill} ${styles.pillHigh}`}>No</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Exactitud de rol" : "Signal-role accuracy"}</div><div>{pct(current.aggregate.meanSignalRoleAccuracy)}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Exactitud de tipo" : "Signal-type accuracy"}</div><div>{pct(current.aggregate.meanSignalTypeAccuracy)}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "F1 exacto de evidencia" : "Evidence exact F1"}</div><div>{current.aggregate.meanEvidenceExactF1.toFixed(3)}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "F1 de soporte de evidencia" : "Evidence support F1"}</div><div>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</div></div>
            </div>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Interpretación" : "Interpretation"}</strong><br />{isSpanish ? "La cobertura ya es completa, pero el sistema todavía no alcanza los niveles mínimos definidos para detección de señales y correspondencia de evidencia. Por eso la siguiente etapa permanece deshabilitada." : "Coverage is complete, but the system has not yet reached the minimum levels defined for signal detection and evidence matching. Therefore, the next stage remains disabled."}</div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Detección global de señales" : "Overall signal detection"}</h2>
            <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10,marginTop:12}}>
              <div style={{background:"#e8f8ec",color:"#123b22",borderRadius:12,padding:24,textAlign:"center"}}><div className={styles.metricValue}>{micro.tp}</div><strong>{isSpanish ? "Detectadas correctamente" : "Correctly detected"}</strong></div>
              <div style={{background:"#fff3d5",color:"#6b4500",borderRadius:12,padding:24,textAlign:"center"}}><div className={styles.metricValue}>{micro.fp}</div><strong>{isSpanish ? "Señales de más" : "Extra signals"}</strong></div>
              <div style={{background:"#ffeaea",color:"#7f1d1d",borderRadius:12,padding:24,textAlign:"center"}}><div className={styles.metricValue}>{micro.fn}</div><strong>{isSpanish ? "Señales omitidas" : "Missed signals"}</strong></div>
            </div>
            <div className={styles.summaryList} style={{marginTop:16}}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Señales esperadas" : "Gold signals"}</div><div>{micro.goldSignals}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Señales producidas" : "Predicted signals"}</div><div>{micro.predictedSignals}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Precisión" : "Precision"}</div><div><strong>{micro.precision.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Recall</div><div><strong>{micro.recall.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Micro F1</div><div><strong>{micro.f1.toFixed(3)}</strong></div></div>
            </div>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Qué significa" : "What it means"}</strong><br />{isSpanish ? "El recall de 0.90 indica que OETI encuentra casi todas las señales esperadas. El problema principal es la precisión: aparecen 14 señales adicionales que el gold standard no considera válidas." : "Recall of 0.90 means OETI finds nearly all expected signals. The main problem is precision: 14 additional signals are produced that the gold standard does not consider valid."}</div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Métricas observadas vs. objetivos" : "Observed metrics vs. targets"}</h2>
            <table className={styles.table}><thead><tr><th>{isSpanish ? "Métrica" : "Metric"}</th><th>{isSpanish ? "Observado" : "Observed"}</th><th>{isSpanish ? "Objetivo" : "Target"}</th><th>{isSpanish ? "Estado" : "Status"}</th></tr></thead><tbody>{thresholdRows.map(([label,observed,threshold]) => <tr key={label}><td>{label}</td><td><strong>{observed.toFixed(3)}</strong></td><td>≥ {threshold.toFixed(2)}</td><td><span className={`${styles.pill} ${observed>=threshold?styles.pillReviewed:styles.pillHigh}`}>{observed>=threshold?(isSpanish?"Cumple":"Pass"):(isSpanish?"Aún no cumple":"Below target")}</span></td></tr>)}</tbody></table>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Calidad de la evidencia vinculada" : "Evidence-linking quality"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "F1 exacto" : "Exact F1"}</div><div><strong>{current.aggregate.meanEvidenceExactF1.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "F1 de soporte equivalente" : "Support-equivalent F1"}</div><div><strong>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Objetivo" : "Target"}</div><div>≥ {current.releaseGate.thresholds.meanEvidenceSupportF1.toFixed(2)}</div></div>
            </div>
            <ul className={styles.insights}>
              <li>{isSpanish ? "OETI suele identificar el contenido correcto, pero no siempre selecciona exactamente el mismo fragmento textual que el gold standard." : "OETI often identifies the correct content, but does not always select exactly the same supporting text span as the gold standard."}</li>
              <li>{isSpanish ? "Cuando se acepta evidencia equivalente por significado, el resultado mejora, pero sigue por debajo del objetivo." : "When semantically equivalent evidence is accepted, the result improves, but remains below target."}</li>
              <li>{isSpanish ? "La prioridad de desarrollo es mejorar la correspondencia entre evidencia, claim y señal sin perder el recall alto." : "The development priority is to improve the correspondence between evidence, claim and signal without losing high recall."}</li>
            </ul>
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
              <li><strong>BEN SE18:</strong> {isSpanish ? "4 TP, 4 FP, 1 FN, F1 0.615 — es el documento con mayor carga de señales adicionales." : "4 TP, 4 FP, 1 FN, F1 0.615 — this document has the highest burden of extra signals."}</li>
              <li><strong>{isSpanish ? "Roedores Mendoza" : "Mendoza rodents"}:</strong> {isSpanish ? "3 TP, 2 FP, 1 FN, F1 0.667 — la evidencia negativa y el contexto de viaje siguen siendo difíciles de representar correctamente." : "3 TP, 2 FP, 1 FN, F1 0.667 — negative evidence and travel-history context remain difficult to represent correctly."}</li>
              <li><strong>{isSpanish ? "Notificación inicial" : "Initial notification"}:</strong> 6 TP, 3 FP, 1 FN, F1 0.750.</li>
              <li><strong>BEN SE17:</strong> {isSpanish ? "6 TP, 1 FP, 0 FN, F1 0.923 — mejor desempeño a nivel documento." : "6 TP, 1 FP, 0 FN, F1 0.923 — strongest document-level performance."}</li>
            </ul>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Prioridad de desarrollo" : "Development priority"}</strong><br />{isSpanish ? "Reducir señales redundantes o excesivamente separadas y mejorar la evidencia asociada a cada señal, preservando el recall alto y la clasificación correcta de tipo y rol." : "Reduce redundant or over-split signals and improve the evidence attached to each signal while preserving high recall and correct type/role classification."}</div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Por qué la evaluación completa es más exigente" : "Why the full evaluation is harder"}</h2>
            <table className={styles.table}><thead><tr><th>{isSpanish ? "Corrida" : "Run"}</th><th>{isSpanish ? "Cobertura" : "Coverage"}</th><th>Signal F1</th><th>Evidence F1</th></tr></thead><tbody><tr><td><strong>Historical corpus runner v0.41</strong></td><td>{historicalPartial.coverage}</td><td>{historicalPartial.meanSignalF1.toFixed(3)}</td><td>{historicalPartial.meanEvidenceF1.toFixed(3)}</td></tr><tr><td><strong>Full corpus v0.4.4</strong></td><td>6/6</td><td>{current.aggregate.meanSignalF1.toFixed(3)}</td><td>{current.aggregate.meanEvidenceSupportF1.toFixed(3)}</td></tr></tbody></table>
            <div className={styles.detailPanel}>{isSpanish ? "El resultado histórico perfecto correspondía a un único documento sencillo. La evaluación completa incorpora transmisión, genómica, fauna, evidencia negativa y movilidad; por eso ofrece una medición mucho más representativa del sistema real." : "The historical perfect result covered one simple document. Full evaluation adds transmission, genomics, wildlife, negative evidence and mobility, making it a much more representative measure of the real system."}</div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}><h2>{isSpanish ? "Configuración del benchmark" : "Benchmark configuration"}</h2><div className={styles.summaryList}>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Código de caso" : "Case code"}</div><div>{current.caseCode}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Versión benchmark" : "Benchmark version"}</div><div>{current.benchmarkVersion}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Documentos configurados" : "Configured documents"}</div><div>{mvHondiusBenchmark.documentCount}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Arquitectura de predicción" : "Prediction architecture"}</div><div style={{overflowWrap:"anywhere"}}>{current.predictionArchitecture}</div></div>
          </div></section>
          <section className={styles.card}><h2>{isSpanish ? "Procedencia de la evaluación" : "Evaluation provenance"}</h2><div className={styles.summaryList}>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Origen" : "Source"}</div><div>{isSpanish ? "Corrida local real de evaluate-corpus" : "Real local evaluate-corpus run"}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Archivo detallado" : "Detailed output"}</div><div style={{overflowWrap:"anywhere"}}>{current.provenance.sourceReport}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Representación en la demo" : "Demo representation"}</div><div>{isSpanish ? "Resumen versionado de métricas agregadas y por documento" : "Versioned summary of aggregate and document-level metrics"}</div></div>
          </div></section>
        </div>
      </div>
    </DemoShell>
  );
}
