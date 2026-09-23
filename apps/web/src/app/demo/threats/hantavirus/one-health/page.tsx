"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "../../../demo-shell";
import { useDemoPreferences } from "../../../demo-preferences";
import { mvHondiusBenchmark } from "../../../mv-hondius-data";
import styles from "../../../demo.module.css";

export default function OneHealthConvergencePage() {
  const { isSpanish } = useDemoPreferences();

  const domainRows = isSpanish ? [
    { domain: "Humana", tone: styles.pillHuman, evidence: "Cluster, casos confirmados/probables, muertes y transmisión persona-persona probable a bordo del MV Hondius.", documents: "04 may · 12 may · 19 may · 26 may", status: "Evidencia directa sólida" },
    { domain: "Fauna silvestre", tone: styles.pillAnimal, evidence: "Investigaciones de campo en Ushuaia y Malargüe, con Abrothrix seropositivos y serología negativa en roedores.", documents: "19 may · 29 jun · 08 jul", status: "Evidencia positiva + negativa" },
    { domain: "Genómica", tone: styles.pillEnv, evidence: "Caracterización de virus Andes y una variante distinta de Orthohantavirus andesense en fauna de Ushuaia; el contexto genómico ayudó a refutar un vínculo causal simple.", documents: "12 may · 19 may · 26 may · 29 jun", status: "Evidencia para probar relaciones" },
    { domain: "Movilidad", tone: styles.pillMedium, evidence: "El antecedente de viaje a Malargüe se conserva como contexto epidemiológico, no como ubicación confirmada de infección.", documents: "08 jul", status: "Evidencia contextual" },
  ] : [
    { domain: "Human", tone: styles.pillHuman, evidence: "Cluster, confirmed/probable cases, deaths and probable person-to-person transmission aboard MV Hondius.", documents: "04 May · 12 May · 19 May · 26 May", status: "Strong direct evidence" },
    { domain: "Wildlife", tone: styles.pillAnimal, evidence: "Field investigations in Ushuaia and Malargüe, including seropositive Abrothrix rodents and negative rodent serology.", documents: "19 May · 29 Jun · 08 Jul", status: "Positive + negative evidence" },
    { domain: "Genomic", tone: styles.pillEnv, evidence: "Andes-virus characterization and a distinct Orthohantavirus andesense variant in Ushuaia wildlife; genomic context helped refute a simple causal link.", documents: "12 May · 19 May · 26 May · 29 Jun", status: "Relationship-testing evidence" },
    { domain: "Mobility", tone: styles.pillMedium, evidence: "Travel history in Malargüe retained as contextual exposure history, not as a confirmed infection location.", documents: "08 Jul", status: "Contextual evidence" },
  ];

  const convergenceRows = mvHondiusBenchmark.documents.map((doc) => ({ date: doc.date, label: doc.label, human: doc.domains.includes("human"), wildlife: doc.domains.includes("wildlife"), genomic: doc.domains.includes("genomic"), mobility: doc.domains.includes("mobility"), relation: doc.relation }));

  return (
    <DemoShell active="threats">
      <div className={styles.content}>
        <PrototypeNote>{isSpanish ? "Vista One Health de caso real — esta pantalla usa únicamente dominios y relaciones adjudicados en los seis documentos del corpus gold standard MV Hondius. No se agrega un dominio ambiental porque no existe una señal ambiental adjudicada en este corpus." : "Real-case One Health view — this screen uses only domains and relationships adjudicated in the six-document MV Hondius gold-standard corpus. No environmental-domain signal is added because none is adjudicated in this corpus."}</PrototypeNote>
        <div className={styles.breadcrumb}><Link href="/demo/threats/hantavirus">{isSpanish ? "Amenazas" : "Threats"}</Link> › MV Hondius › {isSpanish ? "Vista One Health" : "One Health View"}</div>
        <div className={styles.pageHead}>
          <div><h1>{isSpanish ? "MV Hondius — convergencia de evidencia One Health" : "MV Hondius — One Health evidence convergence"}</h1><p className={styles.subtitle}>{isSpanish ? "Evidencia humana · fauna silvestre · genómica · movilidad, incluidos hallazgos negativos y refutados." : "Human · Wildlife · Genomic · Mobility evidence, including negative and refuted findings."}</p></div>
          <div className={styles.actions}><Link className={styles.button} href="/demo/threats/hantavirus">← {isSpanish ? "Explorador de amenazas" : "Threat Explorer"}</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/signals/asm-01">{isSpanish ? "Abrir señal de fauna →" : "Open wildlife signal →"}</Link></div>
        </div>

        <section className={styles.grid4}>{domainRows.map((row) => <article className={styles.card} key={row.domain}><div style={{display:"flex",justifyContent:"space-between",gap:10,alignItems:"flex-start"}}><h3>{row.domain}</h3><span className={`${styles.pill} ${row.tone}`}>{row.status}</span></div><p className={styles.small}>{row.evidence}</p><div className={`${styles.small} ${styles.muted}`}>{isSpanish ? "Documentos" : "Documents"}: {row.documents}</div></article>)}</section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Modelo de convergencia" : "Convergence model"}</h2>
            <div style={{display:"grid",gap:12}}>
              <div className={styles.detailPanel}><strong>{isSpanish ? "Evidencia del brote humano" : "Human outbreak evidence"}</strong><p className={styles.small}>{isSpanish ? "El evento comienza como una señal de brote humano: cluster, muertes, casos confirmados/probables y luego una hipótesis probable de transmisión persona-persona." : "The event begins as a human outbreak signal: cluster, deaths, confirmed/probable cases and later a probable person-to-person transmission hypothesis."}</p></div>
              <div className={styles.detailPanel}><strong>{isSpanish ? "Investigación de fauna silvestre" : "Wildlife investigation"}</strong><p className={styles.small}>{isSpanish ? "Los datos de fauna agregan plausibilidad biológica y evidencia de circulación local, pero no identifican automáticamente la fuente del brote." : "Wildlife data add biological plausibility and local circulation evidence, but they do not automatically identify the outbreak source."}</p></div>
              <div className={styles.detailPanel}><strong>{isSpanish ? "Discriminación genómica" : "Genomic discrimination"}</strong><p className={styles.small}>{isSpanish ? "Los hallazgos genómicos ayudan a comparar relaciones entre virus humanos y de fauna y evitan un vínculo causal no sustentado." : "Genomic findings help compare relationships between human and wildlife viruses and prevent an unsupported causal linkage."}</p></div>
              <div className={styles.detailPanel}><strong>{isSpanish ? "Contexto de movilidad" : "Mobility context"}</strong><p className={styles.small}>{isSpanish ? "El antecedente de viaje aporta contexto epidemiológico, pero OETI lo mantiene separado de una exposición confirmada." : "Travel history supplies epidemiological context, but OETI keeps it separate from confirmed exposure."}</p></div>
              <div className={styles.detailPanel}><strong>{isSpanish ? "Conclusión One Health" : "One Health conclusion"}</strong><br />{isSpanish ? "El valor analítico no es un puntaje numérico de One Health; es la reconciliación explícita de evidencia entre dominios, incertidumbre, resultados negativos e hipótesis refutadas." : "The analytical value is not a numeric “One Health score”; it is the explicit reconciliation of cross-domain evidence, uncertainty, negative results and refuted hypotheses."}</div>
            </div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Relaciones críticas" : "Critical relationships"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Human ↔ Human</div><div>{isSpanish ? <>Transmisión persona-persona a bordo: <strong>probable</strong>, no confirmada.</> : <>Person-to-person transmission aboard the vessel: <strong>probable</strong>, not confirmed.</>}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Wildlife → Human</div><div>{isSpanish ? <>Para los roedores analizados en Ushuaia, la relación como fuente del brote fue <strong>refutada</strong>.</> : <>For the analysed Ushuaia rodents, the outbreak-source relationship was <strong>refuted</strong>.</>}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Genomic ↔ Outbreak</div><div>{isSpanish ? "La similitud/diferencia genómica informa relación, pero no se trata como prueba de origen geográfico." : "Genomic similarity/difference informs relatedness but is not treated as proof of geographic origin."}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>Mobility ↔ Exposure</div><div>{isSpanish ? "Malargüe se conserva como antecedente de viaje; la exposición confirmada sigue sin resolverse." : "Malargüe is retained as travel history; confirmed exposure remains unresolved."}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Ambiente" : "Environment"}</div><div>{isSpanish ? "No hay una señal del dominio ambiental adjudicada en este corpus de seis documentos." : "No environmental-domain signal is adjudicated in this six-document corpus."}</div></div>
            </div>
          </section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}><h2>{isSpanish ? "Matriz de documentos entre dominios" : "Cross-domain document matrix"}</h2><table className={styles.table}><thead><tr><th>{isSpanish?"Fecha":"Date"}</th><th>{isSpanish?"Documento":"Document"}</th><th>{isSpanish?"Humana":"Human"}</th><th>{isSpanish?"Fauna":"Wildlife"}</th><th>{isSpanish?"Genómica":"Genomic"}</th><th>{isSpanish?"Movilidad":"Mobility"}</th><th>{isSpanish?"Rol de evidencia":"Evidence role"}</th></tr></thead><tbody>{convergenceRows.map((row)=><tr key={row.date}><td>{row.date}</td><td>{row.label}</td><td>{row.human?"●":"—"}</td><td>{row.wildlife?"●":"—"}</td><td>{row.genomic?"●":"—"}</td><td>{row.mobility?"●":"—"}</td><td>{row.relation}</td></tr>)}</tbody></table></section>

        <section className={`${styles.card} ${styles.tableWrap}`}><h2>{isSpanish ? "Por qué importa la convergencia" : "Why the convergence matters"}</h2><ul className={styles.insights}><li>{isSpanish ? "Una misma investigación puede contener simultáneamente hallazgos positivos verdaderos y hallazgos negativos verdaderos." : "The same investigation can contain simultaneously true positive findings and true negative findings."}</li><li>{isSpanish ? "La proximidad entre dominios no equivale a causalidad: fauna seropositiva en Ushuaia no estableció la fuente del brote humano." : "Cross-domain proximity does not equal causality: seropositive wildlife in Ushuaia did not establish the source of the human outbreak."}</li><li>{isSpanish ? "La genómica ayuda a discriminar relaciones y evita sobreinterpretar coincidencias geográficas." : "Genomics helps discriminate relatedness and prevents overinterpretation of geographic coincidence."}</li><li>{isSpanish ? "OETI debe mostrar la incertidumbre de forma explícita en lugar de forzar cada señal dentro de una única narrativa explicativa." : "OETI should surface uncertainty explicitly instead of forcing every signal into a single explanatory narrative."}</li></ul></section>
      </div>
    </DemoShell>
  );
}
