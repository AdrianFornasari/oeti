"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { useDemoPreferences } from "../../demo-preferences";
import { useDemoReviewState, type DemoReviewDecision } from "../../demo-review-state";
import { ushuaiaRodentContext, ushuaiaRodentSignal } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

type Decision = DemoReviewDecision | null;

export default function AnalystReviewPage() {
  const signal = ushuaiaRodentSignal;
  const { isSpanish } = useDemoPreferences();
  const { record, saveRecord, clearRecord } = useDemoReviewState(signal.id);
  const [decision, setDecision] = useState<Decision>(null);
  const [submitted, setSubmitted] = useState(false);
  const [comment, setComment] = useState("");
  const [correctedSummary, setCorrectedSummary] = useState<string>(signal.summary);
  const [correctedType, setCorrectedType] = useState<string>(signal.signalType);
  const [correctedRole, setCorrectedRole] = useState<string>(signal.signalRole);

  const decisionDetails = useMemo(() => ({
    confirm: isSpanish ? {
      title: "Confirmar señal",
      status: "analyst_confirmed" as const,
      summary: "La señal ensamblada se acepta como respaldada por el claim atómico citado.",
      effects: [
        "Mantener el claim atómico c1 sin cambios.",
        "Mantener ASM-01 en el conjunto operativo de señales.",
        "Registrar la confirmación del analista en el estado demo.",
        "No inferir causalidad con el brote: el claim c4 sigue refutando ese vínculo para los animales analizados.",
      ],
    } : {
      title: "Confirm signal",
      status: "analyst_confirmed" as const,
      summary: "The assembled signal is accepted as supported by the cited atomic claim.",
      effects: [
        "Keep atomic claim c1 unchanged.",
        "Keep ASM-01 in the operational signal set.",
        "Record analyst confirmation in demo state.",
        "Do not infer outbreak causation; claim c4 still refutes that link for the analysed rodents.",
      ],
    },
    correct: isSpanish ? {
      title: "Corregir señal",
      status: "analyst_corrected" as const,
      summary: "La evidencia de origen se conserva y la corrección del analista se aplica como un override auditable.",
      effects: [
        "Preservar el claim atómico original y el texto fuente.",
        "Guardar la corrección separada de la extracción automática.",
        "Marcar conceptualmente la señal para reensamblado / actualización downstream.",
        "Mantener intacta la evidencia causal negativa independiente c4.",
      ],
    } : {
      title: "Correct signal",
      status: "analyst_corrected" as const,
      summary: "The source evidence is retained while analyst-entered corrections are applied as an auditable override.",
      effects: [
        "Preserve the original atomic claim and source text.",
        "Store the analyst correction separately from the machine extraction.",
        "Conceptually flag the signal for reassembly / downstream refresh.",
        "Keep independent negative causal evidence c4 intact.",
      ],
    },
    reject: isSpanish ? {
      title: "Rechazar señal",
      status: "analyst_rejected" as const,
      summary: "La fuente y el claim extraído siguen siendo trazables, pero la señal no se usaría como inteligencia operativa aceptada.",
      effects: [
        "Preservar documento fuente y extracción original para auditoría.",
        "Marcar ASM-01 como rechazada por un analista.",
        "Excluirla de las vistas demo de inteligencia aceptada.",
        "No eliminar claims relacionados ni señales independientes del mismo documento.",
      ],
    } : {
      title: "Reject signal",
      status: "analyst_rejected" as const,
      summary: "The source and extracted claim remain traceable, but this signal would not be used as accepted operational intelligence.",
      effects: [
        "Preserve the source document and original extraction for auditability.",
        "Mark ASM-01 as analyst rejected.",
        "Exclude it from demo accepted-intelligence views.",
        "Do not delete related claims or independent signals from the same document.",
      ],
    },
  }), [isSpanish]);

  const selectedDecision = decision ? decisionDetails[decision] : null;

  const chooseDecision = (next: DemoReviewDecision) => {
    setDecision(next);
    setSubmitted(false);
  };

  const applyDecision = () => {
    if (!decision) return;
    const detail = decisionDetails[decision];
    saveRecord({
      signalId: signal.id,
      decision,
      status: detail.status,
      note: comment.trim(),
      ...(decision === "correct" ? {
        correctedSummary,
        correctedType,
        correctedRole,
      } : {}),
    });
    setSubmitted(true);
  };

  return (
    <DemoShell active="evaluation">
      <div className={styles.content}>
        <PrototypeNote>
          {isSpanish
            ? "Demo para sponsor — la decisión del analista se conserva únicamente en localStorage de este navegador para demostrar el flujo máquina → revisión humana. No se escribe en producción ni se modifica el gold standard."
            : "Sponsor demo — the analyst decision is stored only in this browser localStorage to demonstrate the machine → human-review flow. No production write occurs and the gold standard is not modified."}
        </PrototypeNote>

        <div className={styles.breadcrumb}>
          <Link href="/demo/evidence/asm-01">{isSpanish ? "Evidencia" : "Evidence"}</Link> › {isSpanish ? "Revisión del analista" : "Analyst Review"} › {signal.shortId}
        </div>

        <div className={styles.pageHead}>
          <div>
            <h1>{isSpanish ? "Revisión del analista" : "Analyst Review"}</h1>
            <p className={styles.subtitle}>{isSpanish ? "La máquina propone; la evidencia se conserva; el analista adjudica." : "The machine proposes; evidence is preserved; the analyst adjudicates."}</p>
          </div>
          <div className={styles.actions}>
            <Link className={styles.button} href="/demo/evidence/asm-01">← {isSpanish ? "Evidencia" : "Evidence"}</Link>
            <Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/signals/asm-01">{isSpanish ? "Ver señal →" : "View signal →"}</Link>
          </div>
        </div>

        <section className={styles.card}>
          <div className={styles.pageHead} style={{ marginBottom: 0 }}>
            <div>
              <div className={styles.small}>{isSpanish ? "OBJETIVO DE REVISIÓN · SEÑAL" : "REVIEW TARGET · SIGNAL"} {signal.shortId}</div>
              <h2 style={{ marginTop: 4 }}>{isSpanish ? <>5 roedores <em>Abrothrix</em> con anticuerpos específicos contra hantavirus</> : <>5 <em>Abrothrix</em> rodents with hantavirus-specific antibodies</>}</h2>
              <p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Ensamblada determinísticamente desde el claim atómico c1." : "Deterministically assembled from atomic claim c1."}</p>
            </div>
            <div>
              <span className={`${styles.pill} ${styles.pillAnimal}`}>{isSpanish ? "Fauna silvestre" : "Wildlife"}</span>{" "}
              <span className={`${styles.pill} ${record ? styles.pillReviewed : styles.pillActive}`}>
                {record ? (isSpanish ? "Revisada" : "Reviewed") : (isSpanish ? "Pendiente" : "Pending")}
              </span>
            </div>
          </div>
        </section>

        <div className={styles.threatLayout} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Propuesta de la máquina" : "Machine proposal"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Resumen" : "Summary"}</div><div>{isSpanish ? "Cinco roedores del género Abrothrix presentaron anticuerpos específicos contra hantavirus en Ushuaia (Tierra del Fuego)." : signal.summary}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Tipo" : "Type"}</div><div>{signal.signalType}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Rol" : "Role"}</div><div>{signal.signalRole}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Confianza" : "Confidence"}</div><div>{Math.round(signal.extractionConfidence * 100)}%</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Fuente" : "Source"}</div><div>{signal.source.label}</div></div>
            </div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Evidencia considerada" : "Evidence considered"}</h2>
            <div style={{ display: "grid", gap: 10 }}>
              <article style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 12 }}><strong>Claim c1 · {isSpanish ? "hallazgo positivo" : "positive finding"}</strong><blockquote style={{ margin: "8px 0 0" }}>“{signal.evidence}”</blockquote></article>
              <article style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 12 }}><strong>Claim {ushuaiaRodentContext.samplingSignal.claimId} · {isSpanish ? "contexto de muestreo" : "sampling context"}</strong><p>{isSpanish ? "Durante los operativos de campo se capturaron 144 roedores silvestres." : ushuaiaRodentContext.samplingSignal.summary}</p></article>
              <article style={{ border: "1px solid #a76464", borderRadius: 10, padding: 12, background: "var(--surface-soft)" }}><strong>Claim {ushuaiaRodentContext.causalNegativeSignal.claimId} · {isSpanish ? "evidencia causal negativa" : "negative causal evidence"}</strong><p>{isSpanish ? "Los roedores analizados fueron descartados como fuente de infección vinculada al brote MV Hondius." : ushuaiaRodentContext.causalNegativeSignal.summary}</p></article>
            </div>
          </section>

          <aside className={styles.card}>
            <h2>{isSpanish ? "Estado humano actual" : "Current human state"}</h2>
            {record ? (
              <div className={styles.summaryList}>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Decisión" : "Decision"}</div><div><strong>{record.status}</strong></div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Backend" : "Backend"}</div><div>{isSpanish ? "No escrito" : "Not written"}</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Persistencia" : "Persistence"}</div><div>localStorage</div></div>
              </div>
            ) : <div className={styles.detailPanel}>{isSpanish ? "Aún no existe una decisión humana en este navegador." : "No human decision exists in this browser yet."}</div>}
          </aside>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Decisión del analista" : "Analyst decision"}</h2>
            <p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "La fuente original y la extracción permanecen trazables en cualquiera de las tres decisiones." : "The original source and extraction remain traceable under all three decisions."}</p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 9 }}>
              <button className={styles.button} onClick={() => chooseDecision("confirm")}>✓ {isSpanish ? "Confirmar" : "Confirm"}</button>
              <button className={styles.button} onClick={() => chooseDecision("correct")}>✎ {isSpanish ? "Corregir" : "Correct"}</button>
              <button className={styles.button} onClick={() => chooseDecision("reject")}>✕ {isSpanish ? "Rechazar" : "Reject"}</button>
            </div>

            {decision === "correct" && (
              <div style={{ marginTop: 14, border: "1px solid var(--border)", background: "var(--surface-soft)", borderRadius: 10, padding: 12 }}>
                <label className={styles.small} htmlFor="corrected-summary"><strong>{isSpanish ? "Resumen corregido" : "Corrected summary"}</strong></label>
                <textarea id="corrected-summary" value={correctedSummary} onChange={(e) => setCorrectedSummary(e.target.value)} style={{ width: "100%", minHeight: 82, marginTop: 6, borderRadius: 9, padding: 10, font: "inherit" }} />
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2,minmax(0,1fr))", gap: 10, marginTop: 10 }}>
                  <label className={styles.small}><strong>{isSpanish ? "Tipo de señal" : "Signal type"}</strong><input value={correctedType} onChange={(e) => setCorrectedType(e.target.value)} style={{ width: "100%", marginTop: 6, borderRadius: 9, padding: 9, font: "inherit" }} /></label>
                  <label className={styles.small}><strong>{isSpanish ? "Rol de señal" : "Signal role"}</strong><input value={correctedRole} onChange={(e) => setCorrectedRole(e.target.value)} style={{ width: "100%", marginTop: 6, borderRadius: 9, padding: 9, font: "inherit" }} /></label>
                </div>
              </div>
            )}

            <label className={styles.small} htmlFor="review-comment" style={{ display: "block", marginTop: 14 }}><strong>{isSpanish ? "Nota del analista" : "Analyst note"}</strong></label>
            <textarea id="review-comment" value={comment} onChange={(e) => setComment(e.target.value)} placeholder={isSpanish ? "Justificación o aclaración opcional…" : "Optional rationale or clarification…"} style={{ width: "100%", minHeight: 80, marginTop: 6, borderRadius: 9, padding: 10, font: "inherit" }} />

            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
              <button disabled={!decision} className={`${styles.button} ${styles.buttonPrimary}`} style={{ opacity: decision ? 1 : .5 }} onClick={applyDecision}>{isSpanish ? "Aplicar decisión demo" : "Apply demo decision"}</button>
              {record && <button className={styles.button} onClick={() => { clearRecord(); setSubmitted(false); }}>{isSpanish ? "Restablecer estado demo" : "Reset demo state"}</button>}
            </div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Impacto downstream" : "Downstream impact"}</h2>
            {!selectedDecision && <div className={styles.detailPanel}>{isSpanish ? "Seleccioná una decisión para previsualizar sus consecuencias." : "Select a decision to preview its consequences."}</div>}
            {selectedDecision && <><div className={styles.detailPanel}><strong>{selectedDecision.title}</strong><br />{selectedDecision.summary}</div><ol className={styles.insights}>{selectedDecision.effects.map((effect) => <li key={effect}>{effect}</li>)}</ol></>}
            {submitted && record && <div className={styles.detailPanel}><strong>{isSpanish ? "Decisión guardada en el navegador" : "Decision saved in browser"}</strong><br />{isSpanish ? "Volvé a Signal Detail para ver cómo cambia el estado operativo mostrado por la demo." : "Return to Signal Detail to see how the demo's displayed operational state changes."}</div>}
          </section>
        </div>
      </div>
    </DemoShell>
  );
}
