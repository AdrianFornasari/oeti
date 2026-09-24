"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { useDemoPreferences } from "../../demo-preferences";
import { useDemoReviewState } from "../../demo-review-state";
import { ushuaiaRodentContext, ushuaiaRodentSignal } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

export default function EvidenceTraceabilityPage() {
  const signal = ushuaiaRodentSignal;
  const { isSpanish } = useDemoPreferences();
  const { record } = useDemoReviewState(signal.id);

  const reviewLabel = !record
    ? (isSpanish ? "Pendiente de revisión" : "Awaiting review")
    : record.decision === "confirm"
      ? (isSpanish ? "Confirmada" : "Confirmed")
      : record.decision === "correct"
        ? (isSpanish ? "Corregida" : "Corrected")
        : (isSpanish ? "Rechazada" : "Rejected");

  const operationalLabel = !record
    ? (isSpanish ? "Aún sin decisión humana" : "No human decision yet")
    : record.decision === "confirm"
      ? (isSpanish ? "Señal aceptada para uso operativo" : "Signal accepted for operational use")
      : record.decision === "correct"
        ? (isSpanish ? "Señal aceptada con corrección humana" : "Signal accepted with human correction")
        : (isSpanish ? "Señal excluida del uso operativo aceptado" : "Signal excluded from accepted operational use");

  const claims = [
    {
      id: signal.directClaim.id,
      kind: "diagnostic_result",
      polarity: "positive",
      summary: isSpanish ? "Cinco roedores del género Abrothrix presentaron anticuerpos específicos contra hantavirus en Ushuaia (Tierra del Fuego)." : signal.summary,
      evidence: signal.evidence,
    },
    {
      id: ushuaiaRodentContext.causalNegativeSignal.claimId,
      kind: "transmission_statement",
      polarity: "negative",
      summary: isSpanish ? "La investigación descartó a los roedores analizados como fuente de infección vinculada al evento MV Hondius." : ushuaiaRodentContext.causalNegativeSignal.summary,
      evidence: ushuaiaRodentContext.causalNegativeSignal.evidence,
    },
    {
      id: ushuaiaRodentContext.samplingSignal.claimId,
      kind: "wildlife_sampling",
      polarity: "positive",
      summary: isSpanish ? "Durante los operativos de campo entre el 18 y el 22 de mayo se capturaron 144 roedores silvestres." : ushuaiaRodentContext.samplingSignal.summary,
      evidence: "Cabe destacar que durante esos operativos se capturaron 144 roedores.",
    },
  ];

  return (
    <DemoShell active="evidence">
      <div className={styles.content}>
        <PrototypeNote>{isSpanish
          ? "Caso real MV Hondius — esta pantalla muestra cómo OETI conserva el recorrido completo desde el texto de una fuente oficial hasta la decisión humana sobre una señal. La decisión de esta demo se guarda solo en este navegador y no altera el corpus adjudicado."
          : "Real MV Hondius case — this screen shows how OETI preserves the complete path from official source text to the human decision on a signal. The demo decision is stored only in this browser and does not alter the adjudicated corpus."}</PrototypeNote>

        <div className={styles.breadcrumb}><Link href="/demo/signals/asm-01">{isSpanish ? "Señales" : "Signals"}</Link> › {signal.shortId} › {isSpanish ? "Trazabilidad de evidencia" : "Evidence Traceability"}</div>

        <div className={styles.pageHead}>
          <div>
            <h1>{isSpanish ? "Trazabilidad de evidencia" : "Evidence Traceability"}</h1>
            <p className={styles.subtitle}>{isSpanish ? "Fuente → afirmaciones extraídas → señal automática → revisión humana → uso operativo." : "Source → extracted claims → machine signal → human review → operational use."}</p>
          </div>
          <div className={styles.actions}>
            <Link className={styles.button} href="/demo/signals/asm-01">← {isSpanish ? "Volver a la señal" : "Back to signal"}</Link>
            <Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/review/asm-01">{isSpanish ? "Revisión del analista →" : "Analyst review →"}</Link>
          </div>
        </div>

        <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 14 }}>
          <article className={styles.card}><h3>1. {isSpanish ? "Documento fuente" : "Source document"}</h3><strong>ANLIS-Malbrán</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Fuente oficial · 29 jun 2026" : "Official source · 29 Jun 2026"}</p></article>
          <article className={styles.card}><h3>2. {isSpanish ? "Afirmaciones extraídas" : "Extracted claims"}</h3><strong>Claims c1 · c4 · c5</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Hallazgo positivo + evidencia causal negativa + muestreo" : "Positive finding + negative causal evidence + sampling"}</p></article>
          <article className={styles.card}><h3>3. {isSpanish ? "Señal automática" : "Machine signal"}</h3><strong>{signal.shortId}</strong><p className={`${styles.small} ${styles.muted}`}>{signal.signalType} · {signal.signalRole}</p></article>
          <article className={styles.card}><h3>4. {isSpanish ? "Revisión humana" : "Human review"}</h3><strong>{reviewLabel}</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Decisión separada y auditable" : "Separate auditable decision"}</p></article>
          <article className={styles.card}><h3>5. {isSpanish ? "Uso operativo" : "Operational use"}</h3><strong>{operationalLabel}</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Cómo se utiliza la señal después de la revisión" : "How the signal is used after review"}</p></article>
        </section>

        <div className={styles.threatLayout} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>{isSpanish ? "1 · Documento fuente" : "1 · Source document"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Fuente" : "Source"}</div><div>{signal.source.label}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Fecha de publicación" : "Publication date"}</div><div>{isSpanish ? "29 jun 2026" : signal.documentDate}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Código de fuente" : "Source code"}</div><div>{signal.source.code}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Caso de evaluación" : "Evaluation case"}</div><div>ARG-HANTA-MV-HONDIUS-2026</div></div>
            </div>
            <div style={{ marginTop: 14, background: "var(--surface-soft)", border: "1px solid var(--border)", borderRadius: 10, padding: 16, lineHeight: 1.65 }}>
              <strong>{isSpanish ? "Fragmento de evidencia" : "Evidence excerpt"}</strong><p>“{signal.evidence}”</p>
            </div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "2 · Afirmaciones extraídas (claims)" : "2 · Extracted claims"}</h2>
            <div style={{ display: "grid", gap: 10 }}>
              {claims.map((claim) => (
                <article key={claim.id} style={{ border: "1px solid var(--border)", borderRadius: 10, padding: 12 }}>
                  <strong>Claim {claim.id}</strong>
                  <div className={`${styles.small} ${styles.muted}`} style={{ margin: "7px 0" }}>{claim.kind} · {isSpanish ? "polaridad" : "polarity"}: {claim.polarity}</div>
                  <div className={styles.small}><strong>{claim.summary}</strong></div>
                  <div className={`${styles.small} ${styles.muted}`} style={{ marginTop: 7 }}>“{claim.evidence}”</div>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "3 · Señal automática" : "3 · Machine signal"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>ID</div><div>{signal.shortId}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Tipo técnico" : "Technical type"}</div><div>{signal.signalType}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Rol técnico" : "Technical role"}</div><div>{signal.signalRole}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Dominio" : "Domain"}</div><div>{isSpanish ? "Fauna silvestre" : "Wildlife"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Confianza de extracción" : "Extraction confidence"}</div><div>{Math.round(signal.extractionConfidence * 100)}%</div></div>
            </div>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Límite causal preservado" : "Preserved causal guardrail"}</strong><br />{isSpanish ? "ASM-01 representa un hallazgo serológico real en fauna. La evidencia causal negativa c4 permanece separada y descarta que los roedores analizados fueran la fuente del brote MV Hondius." : "ASM-01 represents a real wildlife serology finding. Negative causal evidence c4 remains separate and rules out the analysed rodents as the MV Hondius outbreak source."}</div>
          </section>
        </div>

        <div className={styles.dashboardMain} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>{isSpanish ? "4 · Revisión humana" : "4 · Human review"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Estado" : "Status"}</div><div><span className={`${styles.pill} ${record ? styles.pillReviewed : styles.pillActive}`}>{reviewLabel}</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Guardado" : "Saved"}</div><div>{isSpanish ? "Solo en este navegador" : "Only in this browser"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Sistema de producción" : "Production system"}</div><div>{isSpanish ? "Sin cambios" : "Unchanged"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Corpus adjudicado" : "Adjudicated corpus"}</div><div>{isSpanish ? "Sin cambios" : "Unchanged"}</div></div>
            </div>

            {!record && <div className={styles.detailPanel}>{isSpanish ? "La señal todavía no tiene una decisión humana registrada en este navegador. La propuesta automática sigue disponible para revisión." : "The signal does not yet have a human decision recorded in this browser. The machine proposal remains available for review."}</div>}

            {record?.decision === "confirm" && <div className={styles.detailPanel}>{isSpanish ? "El analista confirmó que ASM-01 está respaldada por el claim c1. Esta confirmación no establece causalidad con el brote." : "The analyst confirmed that ASM-01 is supported by claim c1. This confirmation does not establish outbreak causality."}</div>}

            {record?.decision === "correct" && <>
              <div className={styles.detailPanel}>{isSpanish ? "El analista registró una corrección auditable de la señal. La extracción automática original permanece preservada." : "The analyst recorded an auditable correction to the signal. The original machine extraction remains preserved."}</div>
              <div className={styles.summaryList} style={{ marginTop: 12 }}>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Resumen corregido" : "Corrected summary"}</div><div>{record.correctedSummary || "—"}</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Tipo corregido" : "Corrected type"}</div><div>{record.correctedType || "—"}</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Rol corregido" : "Corrected role"}</div><div>{record.correctedRole || "—"}</div></div>
              </div>
            </>}

            {record?.decision === "reject" && <div className={styles.detailPanel}>{isSpanish ? "El analista rechazó ASM-01 para su uso operativo. La fuente, los claims c1, c4 y c5, y la señal automática siguen disponibles para auditoría y evaluación." : "The analyst rejected ASM-01 for operational use. The source, claims c1, c4 and c5, and the machine signal remain available for audit and evaluation."}</div>}

            {record?.note && <div style={{ marginTop: 12 }}><strong>{isSpanish ? "Nota del analista" : "Analyst note"}</strong><p className={styles.small}>{record.note}</p></div>}
            <div style={{ marginTop: 14 }}><Link className={styles.button} href="/demo/review/asm-01">{isSpanish ? "Abrir revisión del analista" : "Open analyst review"}</Link></div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "5 · Uso operativo después de la revisión" : "5 · Operational use after review"}</h2>
            <div className={styles.detailPanel}><strong>{operationalLabel}</strong></div>
            <div className={styles.summaryList} style={{ marginTop: 12 }}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Panel ejecutivo" : "Executive dashboard"}</div><div>{isSpanish ? "Muestra el estado de revisión de ASM-01" : "Displays ASM-01 review state"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Explorador de amenazas" : "Threat Explorer"}</div><div>{isSpanish ? "Muestra la decisión humana junto a la señal" : "Displays the human decision alongside the signal"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Documento fuente" : "Source document"}</div><div>{isSpanish ? "Permanece intacto" : "Remains unchanged"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Claims originales" : "Original claims"}</div><div>{isSpanish ? "Permanecen intactos y auditables" : "Remain intact and auditable"}</div></div>
            </div>
            <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
              <Link className={styles.button} href="/demo">{isSpanish ? "Ver Panel ejecutivo" : "View Dashboard"}</Link>
              <Link className={styles.button} href="/demo/threats/hantavirus">{isSpanish ? "Ver Explorador de amenazas" : "View Threat Explorer"}</Link>
            </div>
          </section>
        </div>

        <section className={styles.card} style={{ marginTop: 14 }}>
          <h2>{isSpanish ? "Principio de trazabilidad OETI" : "OETI traceability principle"}</h2>
          <div className={styles.detailPanel}>{isSpanish ? "Una decisión humana puede cambiar cómo se utiliza una señal, pero no borra ni reescribe la evidencia que la originó. OETI conserva simultáneamente la fuente, las afirmaciones extraídas, la propuesta automática, la decisión humana y el uso operativo resultante." : "A human decision may change how a signal is used, but it does not erase or rewrite the evidence that produced it. OETI preserves the source, extracted claims, machine proposal, human decision and resulting operational use simultaneously."}</div>
        </section>
      </div>
    </DemoShell>
  );
}
