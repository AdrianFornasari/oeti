"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { useDemoPreferences } from "../../demo-preferences";
import { ushuaiaRodentContext, ushuaiaRodentSignal } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

type Decision = "confirm" | "correct" | "reject" | null;

export default function AnalystReviewPage() {
  const signal = ushuaiaRodentSignal;
  const { isSpanish } = useDemoPreferences();
  const [decision, setDecision] = useState<Decision>(null);
  const [submitted, setSubmitted] = useState(false);
  const [comment, setComment] = useState("");
  const [correctedSummary, setCorrectedSummary] = useState(signal.summary);
  const [correctedType, setCorrectedType] = useState(signal.signalType);
  const [correctedRole, setCorrectedRole] = useState(signal.signalRole);

  const decisionDetails = useMemo(() => ({
    confirm: isSpanish ? {
      title: "Confirmar señal", status: "analyst_confirmed", summary: "La señal ensamblada se acepta como respaldada por el claim atómico citado.", effects: ["Mantener el claim atómico c1 sin cambios.", "Mantener ASM-01 en el conjunto operativo de señales.", "Registrar la confirmación del analista en la auditoría.", "No inferir que estos roedores causaron el brote: el claim c4 sigue refutando ese vínculo para los animales analizados."],
    } : {
      title: "Confirm signal", status: "analyst_confirmed", summary: "The assembled signal is accepted as supported by the cited atomic claim.", effects: ["Keep atomic claim c1 unchanged.", "Keep ASM-01 in the operational signal set.", "Record an analyst confirmation in the audit trail.", "Do not infer that these rodents caused the MV Hondius outbreak; claim c4 still refutes that link for the analysed rodents."],
    },
    correct: isSpanish ? {
      title: "Corregir señal", status: "analyst_corrected", summary: "La evidencia de origen se conserva y las correcciones del analista se aplican como un override auditable.", effects: ["Preservar el claim atómico original y el texto fuente.", "Guardar la corrección del analista separada de la extracción automática.", "Marcar la señal para reensamblado determinístico / actualización downstream.", "Mantener intacta la evidencia causal negativa independiente (claim c4)."],
    } : {
      title: "Correct signal", status: "analyst_corrected", summary: "The source evidence is retained while analyst-entered corrections are applied as an auditable override.", effects: ["Preserve the original atomic claim and source text.", "Store the analyst correction separately from the machine extraction.", "Flag the signal for deterministic reassembly / downstream refresh.", "Keep independent negative causal evidence (claim c4) intact."],
    },
    reject: isSpanish ? {
      title: "Rechazar señal", status: "analyst_rejected", summary: "La fuente y el claim extraído siguen siendo trazables, pero esta señal ensamblada no se usaría como inteligencia operativa aceptada.", effects: ["Preservar documento fuente y extracción original para auditoría.", "Marcar ASM-01 como rechazada por un analista.", "Excluir la señal rechazada de las vistas downstream de inteligencia aceptada.", "No eliminar claims relacionados ni señales independientes del mismo documento."],
    } : {
      title: "Reject signal", status: "analyst_rejected", summary: "The source and extracted claim remain traceable, but this assembled signal would not be used operationally as accepted intelligence.", effects: ["Preserve the source document and original extraction for auditability.", "Mark ASM-01 as rejected by an analyst.", "Exclude the rejected signal from accepted downstream intelligence views.", "Do not delete related claims or independent signals from the same document."],
    },
  }), [isSpanish]);

  const selectedDecision = decision ? decisionDetails[decision] : null;
  const chooseDecision = (next: Exclude<Decision, null>) => { setDecision(next); setSubmitted(false); };

  return (
    <DemoShell active="evaluation">
      <div className={styles.content}>
        <PrototypeNote>{isSpanish ? "Demo para sponsor — las acciones de revisión se mantienen solo en el estado del navegador. No se escribe en la base de producción. La evidencia y la señal provienen del corpus adjudicado MV Hondius." : "Sponsor demo — review actions are held only in this browser state. No production database write is performed. The evidence and signal shown below come from the adjudicated MV Hondius corpus."}</PrototypeNote>

        <div className={styles.breadcrumb}><Link href="/demo/evidence/asm-01">{isSpanish ? "Evidencia" : "Evidence"}</Link> › {isSpanish ? "Revisión del analista" : "Analyst Review"} › {isSpanish ? "Señal" : "Signal"} {signal.shortId}</div>
        <div className={styles.pageHead}>
          <div><h1>{isSpanish ? "Revisión del analista" : "Analyst Review"}</h1><p className={styles.subtitle}>{isSpanish ? "Validación humana con consecuencias explícitas sobre claims, señales e inteligencia downstream." : "Human validation with explicit consequences for claims, signals and downstream intelligence."}</p></div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/evidence/asm-01">← {isSpanish ? "Evidencia" : "Evidence"}</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/evaluation">{isSpanish ? "Evaluación del sistema →" : "System evaluation →"}</Link></div>
        </div>

        <section className={styles.card}>
          <div className={styles.pageHead} style={{ marginBottom: 0 }}>
            <div><div className={styles.small}>{isSpanish ? "OBJETIVO DE REVISIÓN · SEÑAL" : "REVIEW TARGET · SIGNAL"} {signal.shortId}</div><h2 style={{ marginTop: 4 }}>{isSpanish ? <>5 roedores <em>Abrothrix</em> con anticuerpos específicos contra hantavirus</> : <>5 <em>Abrothrix</em> rodents with hantavirus-specific antibodies</>}</h2><p className={`${styles.small} ${styles.muted}`} style={{ marginBottom: 0 }}>{isSpanish ? `Ensamblada determinísticamente desde el claim atómico ${signal.directClaim.id} · documento del 29 jun 2026` : `Assembled deterministically from atomic claim ${signal.directClaim.id} · document dated ${signal.documentDate}`}</p></div>
            <div><span className={`${styles.pill} ${styles.pillAnimal}`}>{isSpanish ? "Fauna silvestre" : "Wildlife"}</span>{" "}<span className={`${styles.pill} ${styles.pillActive}`}>{isSpanish ? "Pendiente de revisión" : "Awaiting review"}</span></div>
          </div>
        </section>

        <div className={styles.threatLayout} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Señal extraída" : "Extracted signal"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Resumen" : "Summary"}</div><div>{isSpanish ? "Cinco roedores del género Abrothrix presentaron anticuerpos específicos contra hantavirus en Ushuaia (Tierra del Fuego)." : signal.summary}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Fecha del documento" : "Document date"}</div><div>{isSpanish ? "29 jun 2026" : signal.documentDate}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Fecha del evento" : "Event date"}</div><div>{isSpanish ? "No indicada en esta señal" : "Not stated in this signal"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Ubicación" : "Location"}</div><div>Ushuaia, Tierra del Fuego, Argentina</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Tipo de señal" : "Signal type"}</div><div>{signal.signalType}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Rol de señal" : "Signal role"}</div><div>{signal.signalRole}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Fuente" : "Source"}</div><div>{signal.source.label}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Métrica" : "Metric"}</div><div>{signal.metric.value} {isSpanish ? "animales seropositivos" : "seropositive animals"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Confianza de extracción" : "Extraction confidence"}</div><div>{Math.round(signal.extractionConfidence * 100)}%</div></div>
            </div>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Límite interpretativo" : "Review guardrail"}</strong><br />{isSpanish ? "Confirmar esta señal de laboratorio confirma solamente que la fuente respalda el hallazgo en fauna. No confirma que estos roedores fueran la fuente del brote MV Hondius." : "Confirming this laboratory signal confirms only that the source supports the wildlife finding. It does not confirm that these rodents were the source of the MV Hondius outbreak."}</div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Evidencia considerada" : "Evidence considered"}</h2>
            <div style={{ display: "grid", gap: 10 }}>
              <article style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 12 }}><div className={styles.small}><strong>Claim c1 · {isSpanish ? "resultado diagnóstico positivo" : "positive diagnostic result"}</strong></div><blockquote style={{ margin: "8px 0 0", lineHeight: 1.55 }}>“{signal.evidence}”</blockquote></article>
              <article style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 12 }}><div className={styles.small}><strong>Claim {ushuaiaRodentContext.samplingSignal.claimId} · {isSpanish ? "contexto de muestreo" : "sampling context"}</strong></div><p style={{ marginBottom: 0 }}>{isSpanish ? "Durante los operativos de campo entre el 18 y 22 de mayo se capturaron 144 roedores silvestres." : ushuaiaRodentContext.samplingSignal.summary}</p></article>
              <article style={{ border: "1px solid #a76464", borderRadius: 10, padding: 12, background: "var(--surface-soft)" }}><div className={styles.small}><strong>Claim {ushuaiaRodentContext.causalNegativeSignal.claimId} · {isSpanish ? "evidencia causal negativa" : "negative causal evidence"}</strong></div><p style={{ marginBottom: 6 }}>{isSpanish ? "La investigación descartó a los roedores analizados como fuente de infección vinculada al evento MV Hondius." : ushuaiaRodentContext.causalNegativeSignal.summary}</p><div className={`${styles.small} ${styles.muted}`}>“{ushuaiaRodentContext.causalNegativeSignal.evidence}”</div></article>
            </div>
            <div style={{ marginTop: 14 }}><Link className={styles.button} href="/demo/evidence/asm-01">{isSpanish ? "Abrir trazabilidad completa" : "Open full traceability"}</Link></div>
          </section>

          <aside style={{ display: "grid", gap: 14, alignContent: "start" }}>
            <section className={styles.card}><h2>{isSpanish ? "Cadena de procedencia" : "Provenance chain"}</h2><div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>1. {isSpanish ? "Fuente" : "Source"}</div><div>ANLIS-Malbrán</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>2. Claim</div><div>{signal.directClaim.id} · diagnostic_result</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>3. {isSpanish ? "Ensamblado" : "Assembly"}</div><div>{isSpanish ? "Determinístico" : "Deterministic"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>4. {isSpanish ? "Señal" : "Signal"}</div><div>{signal.shortId} · {signal.signalType}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>5. {isSpanish ? "Revisión" : "Review"}</div><div>{submitted && selectedDecision ? selectedDecision.status : (isSpanish ? "Pendiente" : "Pending")}</div></div>
            </div></section>
            <section className={styles.card}><h2>{isSpanish ? "Estado de revisión" : "Review state"}</h2><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "No se muestran fechas de revisión inventadas. Este panel representa solo el flujo conceptual." : "No fabricated review dates are shown. This panel represents the conceptual workflow only."}</p></section>
          </aside>
        </div>

        <div className={styles.dashboardMain} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Decisión del analista" : "Analyst decision"}</h2>
            <p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Elegí qué debe ocurrir con esta señal ensamblada. La fuente y la extracción original permanecen trazables en todos los caminos." : "Choose what should happen to this assembled signal. The raw source and original extraction remain traceable in every path."}</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 9 }}>
              <button className={styles.button} style={{ background: decision === "confirm" ? "#e8f8ec" : undefined, borderColor: "#65bd7e" }} onClick={() => chooseDecision("confirm")}>✓ {isSpanish ? "Confirmar" : "Confirm"}</button>
              <button className={styles.button} style={{ background: decision === "correct" ? "#fff3d5" : undefined, borderColor: "#e9b64d" }} onClick={() => chooseDecision("correct")}>✎ {isSpanish ? "Corregir" : "Correct"}</button>
              <button className={styles.button} style={{ background: decision === "reject" ? "#ffe7e7" : undefined, borderColor: "#ef7b7b" }} onClick={() => chooseDecision("reject")}>✕ {isSpanish ? "Rechazar" : "Reject"}</button>
            </div>

            {decision === "correct" && <div style={{ marginTop: 14, border: "1px solid var(--border)", background: "var(--surface-soft)", borderRadius: 10, padding: 12 }}>
              <strong>{isSpanish ? "Override de corrección demo" : "Demo correction override"}</strong>
              <p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Estos campos ilustran una capa de corrección del analista. No alteran el corpus adjudicado ni el backend." : "These fields illustrate an analyst correction layer. They do not alter the adjudicated corpus or backend."}</p>
              <label className={styles.small} htmlFor="corrected-summary"><strong>{isSpanish ? "Resumen corregido" : "Corrected summary"}</strong></label><textarea id="corrected-summary" value={correctedSummary} onChange={(e) => setCorrectedSummary(e.target.value)} style={{ width: "100%", minHeight: 82, marginTop: 6, borderRadius: 9, padding: 10, font: "inherit" }} />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2,minmax(0,1fr))", gap: 10, marginTop: 10 }}><label className={styles.small}><strong>{isSpanish ? "Tipo de señal" : "Signal type"}</strong><input value={correctedType} onChange={(e) => setCorrectedType(e.target.value)} style={{ width: "100%", marginTop: 6, borderRadius: 9, padding: 9, font: "inherit" }} /></label><label className={styles.small}><strong>{isSpanish ? "Rol de señal" : "Signal role"}</strong><input value={correctedRole} onChange={(e) => setCorrectedRole(e.target.value)} style={{ width: "100%", marginTop: 6, borderRadius: 9, padding: 9, font: "inherit" }} /></label></div>
            </div>}

            <label className={styles.small} htmlFor="review-comment" style={{ display: "block", marginTop: 14 }}><strong>{isSpanish ? "Nota del analista" : "Analyst note"}</strong></label><textarea id="review-comment" value={comment} onChange={(e) => setComment(e.target.value)} placeholder={isSpanish ? "Justificación o aclaración opcional…" : "Optional rationale or clarification…"} style={{ width: "100%", minHeight: 90, marginTop: 6, borderRadius: 9, padding: 10, font: "inherit" }} />
            <button disabled={!decision} className={`${styles.button} ${styles.buttonPrimary}`} style={{ marginTop: 10, opacity: decision ? 1 : .5 }} onClick={() => setSubmitted(true)}>{isSpanish ? "Aplicar decisión demo" : "Apply demo decision"}</button>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Vista previa del impacto downstream" : "Downstream impact preview"}</h2>
            {!selectedDecision && <div className={styles.detailPanel}>{isSpanish ? "Seleccioná Confirmar, Corregir o Rechazar para ver cómo la revisión humana modifica el flujo de inteligencia." : "Select Confirm, Correct or Reject to preview how human review changes the intelligence workflow."}</div>}
            {selectedDecision && <><div className={styles.detailPanel}><strong>{selectedDecision.title}</strong><br />{selectedDecision.summary}</div><ol className={styles.insights}>{selectedDecision.effects.map((effect) => <li key={effect}>{effect}</li>)}</ol>{decision === "correct" && <pre style={{ whiteSpace: "pre-wrap", overflow: "auto", marginTop: 12, padding: 12, borderRadius: 10, fontSize: 11 }}>{JSON.stringify({ signal_id: signal.id, summary: correctedSummary, signal_type: correctedType, signal_role: correctedRole }, null, 2)}</pre>}</>}
            {submitted && selectedDecision && <div className={styles.detailPanel}><strong>{isSpanish ? "Revisión demo registrada localmente" : "Demo review recorded locally"}</strong><br />{isSpanish ? "Estado" : "Status"}: {selectedDecision.status}<br />{isSpanish ? "Nota de auditoría" : "Audit note"}: {comment.trim() || (isSpanish ? "Sin nota del analista" : "No analyst note supplied")}</div>}
          </section>
        </div>
      </div>
    </DemoShell>
  );
}
