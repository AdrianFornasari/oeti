"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { useDemoPreferences } from "../../demo-preferences";
import { ushuaiaRodentContext, ushuaiaRodentSignal } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

export default function SignalDetailPage() {
  const signal = ushuaiaRodentSignal;
  const { isSpanish } = useDemoPreferences();

  const related = isSpanish ? [
    ["29 jun 2026", "ASM-02", "Los análisis moleculares identificaron una variante de hantavirus no descrita previamente, relacionada con virus Andes y clasificada dentro de Orthohantavirus andesense.", "Fauna silvestre + Genómica", "Observación genómica", "Reportada"],
    ["29 jun 2026", "ASM-03", "La investigación descartó a los roedores analizados como fuente de infección vinculada al evento MV Hondius.", "Humana + Fauna silvestre", "Evidencia negativa", "Reportada"],
    ["18–22 may 2026", "ASM-04", "Durante los operativos de campo se capturaron 144 roedores silvestres.", "Fauna silvestre", "Evento de fauna silvestre", "Reportada"],
  ] : [
    ["29 Jun 2026", "ASM-02", ushuaiaRodentContext.genomicSignal.summary, "Wildlife + Genomic", "Genomic observation", "Reported"],
    ["29 Jun 2026", "ASM-03", ushuaiaRodentContext.causalNegativeSignal.summary, "Human + Wildlife", "Negative evidence", "Reported"],
    ["18–22 May 2026", "ASM-04", ushuaiaRodentContext.samplingSignal.summary, "Wildlife", "Wildlife event", "Reported"],
  ];

  return (
    <DemoShell active="signals">
      <div className={styles.content}>
        <PrototypeNote>{isSpanish
          ? "Esta pantalla usa una extracción real de OETI v0.4.4 del corpus de evaluación MV Hondius. Las etiquetas de presentación siguen simplificadas para uso con sponsor."
          : "This screen now uses a real OETI v0.4.4 extraction from the MV Hondius evaluation corpus. Presentation labels remain simplified for sponsor use."}</PrototypeNote>
        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">{isSpanish ? "Amenazas" : "Threats"}</Link> › Hantavirus › {isSpanish ? "Señal" : "Signal"} {signal.shortId}</div>
        <div className={styles.pageHead}>
          <div>
            <h1>{isSpanish ? <>5 roedores <em>Abrothrix</em> con anticuerpos específicos contra hantavirus</> : <>5 <em>Abrothrix</em> rodents with hantavirus-specific antibodies</>}</h1>
            <p className={styles.subtitle}>{isSpanish ? `Señal ${signal.shortId} · ${signal.signalType} · ${signal.signalRole} · Fauna silvestre` : `Signal ${signal.shortId} · ${signal.signalType} · ${signal.signalRole} · Wildlife`}</p>
          </div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/threats/hantavirus">← {isSpanish ? "Amenaza" : "Threat"}</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/evidence/asm-01">{isSpanish ? "Trazar esta señal →" : "Trace this signal →"}</Link></div>
        </div>

        <div className={styles.threatLayout}>
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
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Precisión geográfica" : "Geographic precision"}</div><div>{isSpanish ? "localidad" : signal.location.precision}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Dominio" : "Domain"}</div><div><span className={`${styles.pill} ${styles.pillAnimal}`}>{isSpanish ? "Fauna silvestre" : "Wildlife"}</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Verificación" : "Verification"}</div><div>{isSpanish ? "reportada" : signal.verificationStatus}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Confianza de extracción" : "Extraction confidence"}</div><div>{Math.round(signal.extractionConfidence * 100)}%</div></div>
            </div>
          </section>

          <aside className={styles.card}>
            <h2>{isSpanish ? "Trazabilidad de la señal" : "Signal traceability"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>1. {isSpanish ? "Fuente" : "Source"}</div><div>{signal.source.label}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>2. {isSpanish ? "Afirmación atómica" : "Atomic claim"}</div><div>{signal.directClaim.id}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>3. {isSpanish ? "Ensamblado" : "Assembly"}</div><div>{isSpanish ? "Determinístico" : "Deterministic"}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>4. {isSpanish ? "Señal" : "Signal"}</div><div>{signal.signalType}</div></div>
            </div>
            <div style={{ marginTop: 14 }}><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/evidence/asm-01">{isSpanish ? "Abrir trazabilidad" : "Open traceability"}</Link></div>
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
