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

  const downstreamLabel = !record
    ? (isSpanish ? "Sin adjudicación humana" : "No human adjudication")
    : record.decision === "confirm"
      ? (isSpanish ? "Incluida como señal aceptada" : "Included as accepted signal")
      : record.decision === "correct"
        ? (isSpanish ? "Incluida con override humano" : "Included with human override")
        : (isSpanish ? "Excluida del uso operativo aceptado" : "Excluded from accepted operational use");

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
          ? "Esta vista muestra la trazabilidad completa de ASM-01 desde la fuente oficial hasta su estado operativo después de la revisión humana. La adjudicación se conserva únicamente en localStorage de esta demo; no modifica el backend ni el gold standard."
          : "This view shows ASM-01 traceability from the official source through its operational state after human review. Adjudication is stored only in this demo browser localStorage; it does not modify the backend or gold standard."}</PrototypeNote>

        <div className={styles.breadcrumb}><Link href="/demo/signals/asm-01">{isSpanish ? "Señales" : "Signals"}</Link> › {signal.shortId} › {isSpanish ? "Trazabilidad de evidencia" : "Evidence Traceability"}</div>

        <div className={styles.pageHead}>
          <div>
            <h1>{isSpanish ? "Trazabilidad de evidencia" : "Evidence Traceability"}</h1>
            <p className={styles.subtitle}>{isSpanish ? "Fuente → claim atómico → señal automática → adjudicación humana → estado downstream." : "Source → atomic claim → machine signal → human adjudication → downstream state."}</p>
          </div>
          <div className={styles.actions}>
            <Link className={styles.button} href="/demo/signals/asm-01">← {isSpanish ? "Volver a la señal" : "Back to signal"}</Link>
            <Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/review/asm-01">{isSpanish ? "Revisión del analista →" : "Analyst review →"}</Link>
          </div>
        </div>

        <section style={{ display: "grid", gridTemplateColumns: "repeat(5,minmax(0,1fr))", gap: 14 }}>
          <article className={styles.card}><h3>1. {isSpanish ? "Documento fuente" : "Source document"}</h3><strong>ANLIS-Malbrán</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Fuente oficial · 29 jun 2026" : "Official source · 29 Jun 2026"}</p></article>
          <article className={styles.card}><h3>2. {isSpanish ? "Claims atómicos" : "Atomic claims"}</h3><strong>c1 · c4 · c5</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Positivo + negativo causal + muestreo" : "Positive + causal negative + sampling"}</p></article>
          <article className={styles.card}><h3>3. {isSpanish ? "Señal de máquina" : "Machine signal"}</h3><strong>{signal.shortId}</strong><p className={`${styles.small} ${styles.muted}`}>{signal.signalType} · {signal.signalRole}</p></article>
          <article className={styles.card}><h3>4. {isSpanish ? "Adjudicación humana" : "Human adjudication"}</h3><strong>{reviewLabel}</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Capa separada y auditable" : "Separate auditable layer"}</p></article>
          <article className={styles.card}><h3>5. {isSpanish ? "Estado downstream" : "Downstream state"}</h3><strong>{downstreamLabel}</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Uso operativo de la señal" : "Operational use of the signal"}</p></article>
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
            <h2>{isSpanish ? "2 · Claims atómicos" : "2 · Atomic claims"}</h2>
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
            <h2>{isSpanish ? "3 · Señal de máquina" : "3 · Machine signal"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "ID" : "ID"}</div><div>{signal.shortId}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Tipo" : "Type"}</div><div>{signal.signalType}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Rol" : "Role"}</div><div>{signal.signalRole}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Dominio" : "Domain"}</div><div>{isSpanish ? "Fauna silvestre" : "Wildlife"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Confianza de extracción" : "Extraction confidence"}</div><div>{Math.round(signal.extractionConfidence * 100)}%</div></div>
            </div>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Límite causal preservado" : "Preserved causal guardrail"}</strong><br />{isSpanish ? "ASM-01 representa un hallazgo serológico real en fauna. El claim c4 permanece separado y refuta que los roedores analizados fueran la fuente del brote MV Hondius." : "ASM-01 represents a real wildlife serology finding. Claim c4 remains separate and refutes the analysed rodents as the MV Hondius outbreak source."}</div>
          </section>
        </div>

        <div className={styles.dashboardMain} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>{isSpanish ? "4 · Adjudicación humana" : "4 · Human adjudication"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Estado" : "Status"}</div><div><span className={`${styles.pill} ${record ? styles.pillReviewed : styles.pillActive}`}>{reviewLabel}</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Persistencia" : "Persistence"}</div><div>localStorage</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Backend" : "Backend"}</div><div>{isSpanish ? "Sin escritura" : "No write"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Gold standard" : "Gold standard"}</div><div>{isSpanish ? "Sin cambios" : "Unchanged"}</div></div>
            </div>

            {!record && <div className={styles.detailPanel}>{isSpanish ? "La señal aún no fue adjudicada en este navegador. La propuesta automática permanece disponible para revisión." : "The signal has not yet been adjudicated in this browser. The machine proposal remains available for review."}</div>}

            {record?.decision === "confirm" && <div className={styles.detailPanel}>{isSpanish ? "El analista confirmó que ASM-01 está respaldada por el claim c1. La confirmación no valida causalidad con el brote." : "The analyst confirmed that ASM-01 is supported by claim c1. Confirmation does not validate outbreak causality."}</div>}

            {record?.decision === "correct" && <>
              <div className={styles.detailPanel}>{isSpanish ? "El analista aplicó un override auditable sobre la representación de la señal. La extracción original sigue preservada." : "The analyst applied an auditable override to the signal representation. The original extraction remains preserved."}</div>
              <div className={styles.summaryList} style={{ marginTop: 12 }}>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Resumen corregido" : "Corrected summary"}</div><div>{record.correctedSummary || "—"}</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Tipo corregido" : "Corrected type"}</div><div>{record.correctedType || "—"}</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Rol corregido" : "Corrected role"}</div><div>{record.correctedRole || "—"}</div></div>
              </div>
            </>}

            {record?.decision === "reject" && <div className={styles.detailPanel}>{isSpanish ? "El analista rechazó ASM-01 para uso operativo aceptado. La fuente, c1, c4, c5 y la señal automática permanecen trazables para auditoría y evaluación." : "The analyst rejected ASM-01 for accepted operational use. The source, c1, c4, c5 and machine signal remain traceable for audit and evaluation."}</div>}

            {record?.note && <div style={{ marginTop: 12 }}><strong>{isSpanish ? "Nota del analista" : "Analyst note"}</strong><p className={styles.small}>{record.note}</p></div>}
            <div style={{ marginTop: 14 }}><Link className={styles.button} href="/demo/review/asm-01">{isSpanish ? "Abrir revisión del analista" : "Open analyst review"}</Link></div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "5 · Estado operativo downstream" : "5 · Downstream operational state"}</h2>
            <div className={styles.detailPanel}><strong>{downstreamLabel}</strong></div>
            <div className={styles.summaryList} style={{ marginTop: 12 }}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Dashboard" : "Dashboard"}</div><div>{isSpanish ? "Muestra el estado de revisión de ASM-01" : "Displays ASM-01 review state"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Threat Explorer" : "Threat Explorer"}</div><div>{isSpanish ? "Propaga la adjudicación como metadato de la señal" : "Propagates adjudication as signal metadata"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Documento fuente" : "Source document"}</div><div>{isSpanish ? "Permanece intacto" : "Remains unchanged"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Claims" : "Claims"}</div><div>{isSpanish ? "Permanecen intactos y auditables" : "Remain intact and auditable"}</div></div>
            </div>
            <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
              <Link className={styles.button} href="/demo">{isSpanish ? "Ver Dashboard" : "View Dashboard"}</Link>
              <Link className={styles.button} href="/demo/threats/hantavirus">{isSpanish ? "Ver Threat Explorer" : "View Threat Explorer"}</Link>
            </div>
          </section>
        </div>

        <section className={styles.card} style={{ marginTop: 14 }}>
          <h2>{isSpanish ? "Principio de trazabilidad OETI" : "OETI traceability principle"}</h2>
          <div className={styles.detailPanel}>{isSpanish ? "Una decisión humana puede cambiar cómo se usa una señal, pero no debe borrar ni reescribir retrospectivamente la evidencia que la originó. OETI conserva simultáneamente la fuente, los claims, la propuesta automática, la adjudicación humana y el estado operativo resultante." : "A human decision may change how a signal is used, but it must not erase or retrospectively rewrite the evidence that produced it. OETI preserves the source, claims, machine proposal, human adjudication and resulting operational state simultaneously."}</div>
        </section>
      </div>
    </DemoShell>
  );
}
