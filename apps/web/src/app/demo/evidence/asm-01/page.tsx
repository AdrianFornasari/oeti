"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { useDemoPreferences } from "../../demo-preferences";
import { ushuaiaRodentContext, ushuaiaRodentSignal } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

export default function EvidenceTraceabilityPage() {
  const signal = ushuaiaRodentSignal;
  const { isSpanish } = useDemoPreferences();

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
          ? "Esta vista de trazabilidad refleja claims atómicos y señales reales del documento ANLIS-Malbrán del 29 de junio de 2026 incluido en el corpus de evaluación MV Hondius."
          : "This traceability view now reflects real atomic claims and signals from the 29 June 2026 ANLIS-Malbrán document in the MV Hondius evaluation corpus."}</PrototypeNote>
        <div className={styles.breadcrumb}><Link href="/demo/signals/asm-01">{isSpanish ? "Señales" : "Signals"}</Link> › {signal.shortId} › {isSpanish ? "Trazabilidad de evidencia" : "Evidence Traceability"}</div>
        <div className={styles.pageHead}>
          <div><h1>{isSpanish ? "Trazabilidad de evidencia" : "Evidence Traceability"}</h1><p className={styles.subtitle}>{isSpanish ? "Desde el texto de la fuente oficial hasta claims atómicos y la señal ensamblada." : "From official source text to atomic claims to assembled signal."}</p></div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/signals/asm-01">← {isSpanish ? "Volver a la señal" : "Back to signal"}</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/review/asm-01">{isSpanish ? "Revisión del analista →" : "Analyst review →"}</Link></div>
        </div>

        <section className={styles.grid4}>
          <article className={styles.card}><h3>1. {isSpanish ? "Documento fuente" : "Source document"}</h3><strong>ANLIS-Malbrán official news</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "29 junio 2026" : "29 June 2026"}</p></article>
          <article className={styles.card}><h3>2. {isSpanish ? "Claims atómicos" : "Atomic claims"}</h3><strong>Claims c1, c4 and c5</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Hallazgo positivo + evidencia causal negativa + muestreo de fauna" : "Positive finding + negative causal evidence + wildlife sampling"}</p></article>
          <article className={styles.card}><h3>3. {isSpanish ? "Ensamblado de señal" : "Signal assembly"}</h3><strong>{isSpanish ? "Ensamblado determinístico" : "Deterministic assembly"}</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Los claims atómicos se ensamblan en señales distintas" : "Atomic claims are assembled into distinct signals"}</p></article>
          <article className={styles.card}><h3>4. {isSpanish ? "Interpretación" : "Interpretation"}</h3><strong>{isSpanish ? "Hallazgo ≠ fuente del brote" : "Finding ≠ outbreak source"}</strong><p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Los roedores analizados fueron descartados como fuente de infección" : "The analysed rodents were ruled out as the infection source"}</p></article>
        </section>

        <div className={styles.threatLayout} style={{ marginTop: 14 }}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Documento fuente" : "Source document"}</h2>
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
            <h2>{isSpanish ? "Claims atómicos" : "Atomic claims"}</h2>
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
            <h2>{isSpanish ? "Qué preserva OETI" : "What OETI preserves"}</h2>
            <ol className={styles.insights}>
              <li>{isSpanish ? <>Evidencia positiva en fauna: cinco roedores <em>Abrothrix</em> tenían anticuerpos específicos contra hantavirus.</> : <>Positive wildlife evidence: five <em>Abrothrix</em> rodents had hantavirus-specific antibodies.</>}</li>
              <li>{isSpanish ? "Contexto de muestreo: se capturaron 144 roedores silvestres durante los operativos del 18 al 22 de mayo." : "Sampling context: 144 wild rodents were captured during operations from 18–22 May."}</li>
              <li>{isSpanish ? "Evidencia causal negativa: los roedores analizados fueron descartados como fuente vinculada al evento MV Hondius." : "Negative causal evidence: the analysed rodents were ruled out as the source linked to the MV Hondius event."}</li>
            </ol>
            <pre style={{ whiteSpace: "pre-wrap", overflow: "auto", padding: 14, borderRadius: 10, fontSize: 11, lineHeight: 1.5 }}>{`{
  "signal_type": "laboratory_result",
  "signal_role": "primary_event",
  "domains": ["wildlife"],
  "host": "Abrothrix",
  "seropositive_animals": 5,
  "location": "Ushuaia",
  "extraction_confidence": 0.80,
  "causal_link_to_mv_hondius": "refuted"
}`}</pre>
          </section>
        </div>
      </div>
    </DemoShell>
  );
}
