"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { useDemoPreferences } from "../../demo-preferences";
import { useDemoReviewState } from "../../demo-review-state";
import { ushuaiaRodentContext, ushuaiaRodentSignal } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

export default function SignalDetailPage() {
  const signal = ushuaiaRodentSignal;
  const { isSpanish } = useDemoPreferences();
  const { record, hydrated } = useDemoReviewState(signal.id);

  const related = isSpanish ? [
    ["29 jun 2026", "ASM-02", "Los análisis moleculares identificaron una variante de hantavirus no descrita previamente, relacionada con virus Andes y clasificada dentro de Orthohantavirus andesense.", "Fauna silvestre + Genómica", "Observación genómica", "Reportada"],
    ["29 jun 2026", "ASM-03", "La investigación descartó a los roedores analizados como fuente de infección vinculada al evento MV Hondius.", "Humana + Fauna silvestre", "Evidencia negativa", "Reportada"],
    ["18–22 may 2026", "ASM-04", "Durante los operativos de campo se capturaron 144 roedores silvestres.", "Fauna silvestre", "Evento de fauna silvestre", "Reportada"],
  ] : [
    ["29 Jun 2026", "ASM-02", ushuaiaRodentContext.genomicSignal.summary, "Wildlife + Genomic", "Genomic observation", "Reported"],
    ["29 Jun 2026", "ASM-03", ushuaiaRodentContext.causalNegativeSignal.summary, "Human + Wildlife", "Negative evidence", "Reported"],
    ["18–22 May 2026", "ASM-04", ushuaiaRodentContext.samplingSignal.summary, "Wildlife", "Wildlife event", "Reported"],
  ];

  const humanSummary = record?.decision === "correct" && record.correctedSummary ? record.correctedSummary : signal.summary;
  const humanType = record?.decision === "correct" && record.correctedType ? record.correctedType : signal.signalType;
  const humanRole = record?.decision === "correct" && record.correctedRole ? record.correctedRole : signal.signalRole;
  const accepted = record?.decision !== "reject";

  const reviewLabel = !hydrated || !record
    ? (isSpanish ? "Sin revisión humana" : "No human review")
    : record.decision === "confirm"
      ? (isSpanish ? "Confirmada por analista" : "Analyst confirmed")
      : record.decision === "correct"
        ? (isSpanish ? "Corregida por analista" : "Analyst corrected")
        : (isSpanish ? "Rechazada por analista" : "Analyst rejected");

  return (
    <DemoShell active="signals">
      <div className={styles.content}>
        <PrototypeNote>{isSpanish
          ? "Esta pantalla combina una extracción real de OETI v0.4.4 con un estado de revisión humana guardado solo en este navegador para la demo. La revisión no modifica el backend ni el gold standard."
          : "This screen combines a real OETI v0.4.4 extraction with browser-local human-review state for the demo. Review does not modify the backend or gold standard."}</PrototypeNote>

        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">{isSpanish ? "Amenazas" : "Threats"}</Link> › Hantavirus › {isSpanish ? "Señal" : "Signal"} {signal.shortId}</div>

        <div className={styles.pageHead}>
          <div>
            <h1>{isSpanish ? <>5 roedores <em>Abrothrix</em> con anticuerpos específicos contra hantavirus</> : <>5 <em>Abrothrix</em> rodents with hantavirus-specific antibodies</>}</h1>
            <p className={styles.subtitle}>{isSpanish ? `Señal ${signal.shortId} · ${signal.signalType} · ${signal.signalRole} · Fauna silvestre` : `Signal ${signal.shortId} · ${signal.signalType} · ${signal.signalRole} · Wildlife`}</p>
          </div>
          <div className={styles.actions}>
            <Link className={styles.button} href="/demo/evidence/asm-01">{isSpanish ? "Evidencia" : "Evidence"}</Link>
            <Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/review/asm-01">{isSpanish ? "Revisión del analista →" : "Analyst review →"}</Link>
          </div>
        </div>

        <section className={styles.card} style={{ marginBottom: 14 }}>
          <div className={styles.pageHead} style={{ marginBottom: 0 }}>
            <div>
              <div className={styles.small}>{isSpanish ? "ESTADO DE INTELIGENCIA" : "INTELLIGENCE STATE"}</div>
              <h2 style={{ marginTop: 4 }}>{reviewLabel}</h2>
              <p className={`${styles.small} ${styles.muted}`} style={{ marginBottom: 0 }}>
                {isSpanish ? "La extracción automática original permanece inmutable y trazable." : "The original machine extraction remains immutable and traceable."}
              </p>
            </div>
            <div>
              <span className={`${styles.pill} ${record ? (accepted ? styles.pillReviewed : styles.pillHigh) : styles.pillActive}`}>
                {record ? (accepted ? (isSpanish ? "Aceptada en demo" : "Accepted in demo") : (isSpanish ? "Excluida de operación" : "Excluded operationally")) : (isSpanish ? "Machine generated" : "Machine generated")}
              </span>
            </div>
          </div>
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Propuesta de la máquina" : "Machine-generated signal"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Resumen" : "Summary"}</div><div>{isSpanish ? "Cinco roedores del género Abrothrix presentaron anticuerpos específicos contra hantavirus en Ushuaia (Tierra del Fuego)." : signal.summary}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Tipo" : "Type"}</div><div>{signal.signalType}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Rol" : "Role"}</div><div>{signal.signalRole}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Confianza de extracción" : "Extraction confidence"}</div><div>{Math.round(signal.extractionConfidence * 100)}%</div></div>
            </div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Estado después de revisión humana" : "Human-reviewed state"}</h2>
            {!record ? (
              <div className={styles.detailPanel}>{isSpanish ? "Todavía no hay una adjudicación humana guardada en este navegador. La señal mostrada es exclusivamente la propuesta automática." : "No human adjudication is stored in this browser yet. The displayed signal is exclusively the machine proposal."}</div>
            ) : record.decision === "reject" ? (
              <>
                <div className={styles.detailPanel}><strong>{isSpanish ? "Rechazada por analista" : "Analyst rejected"}</strong><br />{isSpanish ? "La señal no se considera inteligencia operativa aceptada en la demo, pero la fuente, el claim y la extracción permanecen disponibles para auditoría." : "The signal is not considered accepted operational intelligence in the demo, but source, claim and extraction remain available for audit."}</div>
                {record.note && <p className={styles.small}><strong>{isSpanish ? "Nota" : "Note"}:</strong> {record.note}</p>}
              </>
            ) : (
              <div className={styles.summaryList}>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Estado" : "Status"}</div><div><strong>{record.status}</strong></div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Resumen operativo" : "Operational summary"}</div><div>{record.decision === "correct" ? humanSummary : (isSpanish ? "Hallazgo de fauna confirmado por analista; no implica causalidad con el brote." : "Wildlife finding confirmed by analyst; does not imply outbreak causation.")}</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Tipo" : "Type"}</div><div>{humanType}</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Rol" : "Role"}</div><div>{humanRole}</div></div>
                {record.note && <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Nota del analista" : "Analyst note"}</div><div>{record.note}</div></div>}
              </div>
            )}
          </section>
        </div>

        <div className={styles.threatLayout} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Resumen" : "Summary"}</h2>
            <p>{isSpanish ? "Cinco roedores del género Abrothrix presentaron anticuerpos específicos contra hantavirus en Ushuaia (Tierra del Fuego)." : signal.summary}</p>
            <div className={styles.detailPanel}><strong>{isSpanish ? "Interpretación importante" : "Important interpretation"}</strong><br />{isSpanish
              ? "Esta es una señal real de fauna silvestre detectada durante la investigación, pero OETI también extrajo evidencia negativa que descarta a estos roedores analizados como fuente de infección del brote del MV Hondius."
              : "This is a real wildlife signal detected during the investigation, but OETI also extracted negative evidence ruling out these analysed rodents as the infection source for the MV Hondius outbreak."}</div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Contexto" : "Context"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Fecha del documento" : "Document date"}</div><div>{isSpanish ? "29 jun 2026" : signal.documentDate}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Fecha del evento" : "Event date"}</div><div>{isSpanish ? "No indicada en esta señal" : "Not stated in this signal"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Ubicación" : "Location"}</div><div>{signal.location.locality}, {signal.location.admin1}, {signal.location.country}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Dominio" : "Domain"}</div><div><span className={`${styles.pill} ${styles.pillAnimal}`}>{isSpanish ? "Fauna silvestre" : "Wildlife"}</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Verificación fuente" : "Source verification"}</div><div>{isSpanish ? "reportada" : signal.verificationStatus}</div></div>
            </div>
          </section>

          <aside className={styles.card}>
            <h2>{isSpanish ? "Trazabilidad" : "Traceability"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>1. {isSpanish ? "Fuente" : "Source"}</div><div>{signal.source.label}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>2. Claim</div><div>{signal.directClaim.id}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>3. {isSpanish ? "Ensamblado" : "Assembly"}</div><div>{isSpanish ? "Determinístico" : "Deterministic"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>4. {isSpanish ? "Señal máquina" : "Machine signal"}</div><div>{signal.shortId}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>5. {isSpanish ? "Revisión humana" : "Human review"}</div><div>{record?.status ?? (isSpanish ? "Pendiente" : "Pending")}</div></div>
            </div>
          </aside>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Campos estructurados" : "Structured fields"}</h2>
            <table className={styles.table}><tbody>
              <tr><td>{isSpanish ? "Animales seropositivos" : "Seropositive animals"}</td><td><strong>{signal.metric.value}</strong></td></tr>
              <tr><td>{isSpanish ? "Huésped / género" : "Host / genus"}</td><td><strong>{signal.host}</strong></td></tr>
              <tr><td>{isSpanish ? "Patógeno" : "Pathogen"}</td><td><strong>{signal.pathogen}</strong></td></tr>
              <tr><td>{isSpanish ? "Tipo de prueba" : "Test type"}</td><td><strong>{signal.diagnostics.testType}</strong></td></tr>
              <tr><td>{isSpanish ? "Objetivo" : "Target"}</td><td><strong>{signal.diagnostics.target}</strong></td></tr>
              <tr><td>{isSpanish ? "Resultado" : "Result"}</td><td><strong>{isSpanish ? "positivo" : signal.diagnostics.result}</strong></td></tr>
            </tbody></table>
          </section>
          <section className={styles.card}>
            <h2>{isSpanish ? "Fragmento de evidencia" : "Evidence excerpt"}</h2>
            <blockquote style={{ margin: 0, padding: 16, background: "var(--surface-soft)", borderRadius: 10, lineHeight: 1.55 }}>“{signal.evidence}”</blockquote>
            <p className={`${styles.small} ${styles.muted}`}>{signal.source.label} · {isSpanish ? "fuente oficial incluida en el corpus de evaluación." : "official source included in the evaluation corpus."}</p>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}>
          <h2>{isSpanish ? "Señales extraídas relacionadas del mismo documento" : "Related extracted signals from the same document"}</h2>
          <table className={styles.table}>
            <thead><tr><th>{isSpanish ? "Fecha" : "Date"}</th><th>ID</th><th>{isSpanish ? "Descripción" : "Description"}</th><th>{isSpanish ? "Dominio" : "Domain"}</th><th>{isSpanish ? "Tipo" : "Type"}</th><th>{isSpanish ? "Estado" : "Status"}</th></tr></thead>
            <tbody>{related.map((row) => <tr key={row[1]}>{row.map((cell, index) => <td key={`${row[1]}-${index}`}>{cell}</td>)}</tr>)}</tbody>
          </table>
        </section>
      </div>
    </DemoShell>
  );
}
