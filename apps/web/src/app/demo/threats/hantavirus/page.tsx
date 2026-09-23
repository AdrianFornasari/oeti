"use client";

import Link from "next/link";
import { useState } from "react";
import { DemoShell, PrototypeNote } from "../../demo-shell";
import { useDemoPreferences } from "../../demo-preferences";
import { mvHondiusBenchmark } from "../../mv-hondius-data";
import styles from "../../demo.module.css";

const relationTone = (relation: string) => relation.includes("Negative") ? styles.pillLow : relation.includes("Transmission") ? styles.pillMedium : styles.pillHigh;
const sourceFamilies = new Set(mvHondiusBenchmark.documents.map((doc) => doc.source)).size;

const esDoc = (id: string) => ({
  "doc-2026-05-04": { label: "Notificación inicial y monitoreo nacional", summary: "Monitoreo oficial tras la notificación del 2 de mayo de un cluster de enfermedad respiratoria aguda grave a bordo del MV Hondius, con tres muertes y un pasajero confirmado por laboratorio para hantavirus.", relation: "Evidencia primaria del brote", locationRole: "Ubicación actual del buque", facts: ["3 muertes reportadas", "1 caso de hantavirus confirmado por laboratorio", "Vía de transmisión aún desconocida"] },
  "doc-2026-05-12": { label: "Boletín Epidemiológico Nacional — SE17", summary: "El BEN actualizó el evento a ocho casos identificados: seis confirmados, dos probables y tres muertes. Los hallazgos genómicos se monitorearon sin interpretar similitud genética como prueba del origen del brote.", relation: "Actualización del brote", locationRole: "Monitoreo del brote", facts: ["8 casos identificados", "6 confirmados", "2 probables", "3 muertes"] },
  "doc-2026-05-19": { label: "Boletín Epidemiológico Nacional — SE18", summary: "Al 13 de mayo se habían identificado 11 casos: ocho confirmados por virus Andes, dos probables y uno inconcluso. La evidencia sugirió infección en tierra seguida de transmisión persona-persona probable a bordo.", relation: "Hipótesis de transmisión", locationRole: "Brote e investigación de campo", facts: ["11 casos identificados", "8 confirmados por virus Andes", "2 probables", "1 inconcluso", "Transmisión persona-persona adjudicada como probable"] },
  "doc-2026-05-26": { label: "Boletín Epidemiológico Nacional — SE19", summary: "Se confirmó un nuevo caso por virus Andes entre los pasajeros, llevando el total a nueve confirmados y dos probables.", relation: "Actualización del brote", locationRole: "Monitoreo del brote", facts: ["1 nuevo caso confirmado", "9 casos confirmados en total", "2 probables"] },
  "doc-2026-06-29": { label: "Roedores de Tierra del Fuego — evidencia genómica no relacionada con el brote", summary: "Cinco roedores Abrothrix capturados en Ushuaia presentaron anticuerpos específicos contra hantavirus. Se identificó una variante previamente no descrita de Orthohantavirus andesense, pero los roedores analizados fueron descartados como fuente del brote.", relation: "Evidencia causal negativa", locationRole: "Lugar de muestreo de fauna silvestre", facts: ["144 roedores silvestres capturados", "5 Abrothrix seropositivos", "Variante nueva relacionada con virus Andes", "Vínculo animal-humano refutado para los roedores analizados"] },
  "doc-2026-07-08": { label: "Roedores de Mendoza — evidencia negativa", summary: "Los roedores silvestres capturados cerca de Malargüe no mostraron anticuerpos específicos contra hantavirus. La pareja neerlandesa había estado en la zona antes de embarcar, pero Malargüe se conserva como antecedente de viaje y no como exposición confirmada.", relation: "Evidencia negativa / prueba de hipótesis", locationRole: "Lugar de muestreo y antecedente de viaje", facts: ["Serología negativa en roedores", "Malargüe conservado como antecedente de viaje", "No se infiere una ubicación de exposición confirmada"] },
} as const)[id as keyof ReturnType<typeof esDoc>] as never;

export default function HantavirusThreatPage() {
  const { isSpanish } = useDemoPreferences();
  const [selectedIndex, setSelectedIndex] = useState(0);
  const selected = mvHondiusBenchmark.documents[selectedIndex] ?? mvHondiusBenchmark.documents[0];
  const selectedEs = esDoc(selected.id) as { label:string; summary:string; relation:string; locationRole:string; facts:string[] };

  return (
    <DemoShell active="threats">
      <div className={styles.content}>
        <PrototypeNote>{isSpanish ? "Demo de caso real para sponsor — las seis entradas de la cronología provienen del corpus gold standard adjudicado del MV Hondius. Fecha del documento, fecha del evento/referencia y rol geográfico se muestran por separado para evitar falsa precisión temporal o causal." : "Real-case sponsor demo — the six timeline entries below come from the adjudicated MV Hondius gold-standard corpus. Document date, event/reference date and geographic role are shown separately to avoid false temporal or causal precision."}</PrototypeNote>
        <div className={styles.breadcrumb}><Link href="/demo">Dashboard</Link> › {isSpanish ? "Amenazas" : "Threats"} › MV Hondius hantavirus investigation</div>
        <div className={styles.pageHead}>
          <div><h1>{isSpanish ? "Investigación de hantavirus MV Hondius" : "MV Hondius hantavirus investigation"} <span className={`${styles.pill} ${styles.pillReviewed}`}>{isSpanish ? "Corpus adjudicado" : "Adjudicated corpus"}</span></h1><p className={styles.subtitle}>{isSpanish ? `Caso ${mvHondiusBenchmark.caseCode} · Benchmark gold standard v${mvHondiusBenchmark.benchmarkVersion} · Seis documentos de fuentes oficiales` : `Case ${mvHondiusBenchmark.caseCode} · Gold-standard benchmark v${mvHondiusBenchmark.benchmarkVersion} · Six official-source documents`}</p></div>
          <div className={styles.actions}><Link className={styles.button} href="/demo">← Dashboard</Link><Link className={styles.button} href="/demo/threats/hantavirus/one-health">{isSpanish ? "Vista One Health" : "One Health view"}</Link><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo/signals/asm-01">{isSpanish ? "Abrir señal de fauna →" : "Open wildlife signal →"}</Link></div>
        </div>

        <section className={styles.grid4}>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.blue}`}>6</div><div><span className={styles.metricValue}>6</span><div className={styles.metricLabel}>{isSpanish ? "Documentos adjudicados" : "Adjudicated documents"}</div><small className={styles.muted}>{isSpanish ? "04 may – 08 jul 2026" : "04 May – 08 Jul 2026"}</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.red}`}>11</div><div><span className={styles.metricValue}>11</span><div className={styles.metricLabel}>{isSpanish ? "Máximo de casos identificados" : "Maximum identified cases"}</div><small className={styles.muted}>{isSpanish ? "Reportado al 13 de mayo" : "Reported by 13 May"}</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.green}`}>9</div><div><span className={styles.metricValue}>9</span><div className={styles.metricLabel}>{isSpanish ? "Casos confirmados" : "Confirmed cases"}</div><small className={styles.muted}>{isSpanish ? "Total informado al 26 de mayo" : "Total reported by 26 May"}</small></div></article>
          <article className={`${styles.card} ${styles.metric}`}><div className={`${styles.metricIcon} ${styles.purple}`}>2</div><div><span className={styles.metricValue}>2</span><div className={styles.metricLabel}>{isSpanish ? "Investigaciones con evidencia negativa" : "Negative-evidence investigations"}</div><small className={styles.muted}>{isSpanish ? "Vínculo causal Ushuaia + serología Malargüe" : "Ushuaia causal link + Malargüe serology"}</small></div></article>
        </section>

        <div className={styles.dashboardMain}>
          <section className={styles.card}>
            <h2>{isSpanish ? "Cronología de documentos gold standard" : "Gold-standard document timeline"}</h2>
            <p className={`${styles.small} ${styles.muted}`}>{isSpanish ? "El orden vertical sigue la secuencia de publicación. La fecha epidemiológica del evento/referencia se muestra por separado." : "The vertical order is the document-publication sequence. The epidemiological event/reference date is displayed separately inside each entry."}</p>
            <div className={styles.timeline}>{mvHondiusBenchmark.documents.map((doc,index) => { const es = esDoc(doc.id) as {label:string;summary:string;relation:string}; return <button key={doc.id} className={`${styles.timelineItem} ${selectedIndex===index?styles.timelineSelected:""}`} onClick={() => setSelectedIndex(index)}><div className={styles.timelineLine}><span className={`${styles.timelineNode} ${doc.relation.includes("Negative")?styles.markerAnimal:styles.markerHuman}`} /></div><div className={styles.timelineDate}>{doc.date}</div><div><div className={styles.signalName}>{isSpanish?es.label:doc.label}</div><div className={styles.signalText}>{isSpanish?es.summary:doc.summary}</div><div style={{marginTop:7,display:"flex",gap:6,flexWrap:"wrap"}}><span className={`${styles.pill} ${relationTone(doc.relation)}`}>{isSpanish?es.relation:doc.relation}</span><span className={styles.pill}>{isSpanish?"Evento/referencia":"Event/reference"}: {doc.eventDate}</span></div></div></button>; })}</div>
          </section>

          <section className={styles.card}>
            <h2>{isSpanish ? "Documento seleccionado" : "Selected document"}</h2>
            <div className={styles.summaryList}>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish?"Fecha del documento":"Document date"}</div><div><strong>{selected.date}</strong></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish?"Fecha evento/referencia":"Event/reference date"}</div><div>{selected.eventDate}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish?"Fuente oficial":"Official source"}</div><div>{selected.sourceLabel} <span className={styles.muted}>({selected.source})</span></div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish?"Contexto geográfico":"Location context"}</div><div>{selected.location}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish?"Rol de ubicación":"Location role"}</div><div>{isSpanish?selectedEs.locationRole:selected.locationRole}</div></div>
              <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish?"Rol de evidencia":"Evidence role"}</div><div><span className={`${styles.pill} ${relationTone(selected.relation)}`}>{isSpanish?selectedEs.relation:selected.relation}</span></div></div>
            </div>
            <div className={styles.detailPanel}><strong>{isSpanish?"Interpretación":"Interpretation"}</strong><br />{isSpanish?selectedEs.summary:selected.summary}</div>
            <h3 style={{marginTop:18}}>{isSpanish?"Hechos adjudicados clave":"Key adjudicated facts"}</h3><ul className={styles.insights}>{(isSpanish?selectedEs.facts:selected.keyFacts).map((fact) => <li key={fact}>{fact}</li>)}</ul>
            <div style={{marginTop:16}}><a className={styles.button} href={selected.sourceUrl} target="_blank" rel="noreferrer">{isSpanish?"Abrir fuente oficial ↗":"Open official source ↗"}</a></div>
          </section>
        </div>

        <div className={styles.dashboardMain}>
          <section className={styles.card}><h2>{isSpanish?"Resumen de amenaza — corpus adjudicado":"Threat summary — adjudicated corpus"}</h2><div className={styles.summaryList}>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish?"Brote humano":"Human outbreak"}</div><div>{isSpanish?"Hantavirus por virus Andes a bordo del MV Hondius":"Andes-virus hantavirus aboard MV Hondius"}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish?"Evaluación de transmisión":"Transmission assessment"}</div><div>{isSpanish?"Transmisión persona-persona a bordo adjudicada como probable, no confirmada":"Person-to-person transmission aboard the vessel adjudicated as probable, not confirmed"}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish?"Evidencia de fauna":"Wildlife evidence"}</div><div>{isSpanish?"Hantavirus detectado en Abrothrix de Ushuaia, pero los animales analizados fueron descartados como fuente del brote":"Hantavirus detected in Abrothrix rodents in Ushuaia, but the analysed rodents were ruled out as the outbreak source"}</div></div>
            <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish?"Familias de fuentes":"Source families"}</div><div>{sourceFamilies}: Ministerio de Salud / BEN and ANLIS-Malbrán</div></div>
          </div></section>
          <section className={styles.card}><h2>{isSpanish?"Principio analítico OETI":"OETI analytical principle"}</h2><div className={styles.detailPanel}>{isSpanish?"Hallazgos positivos, hallazgos negativos, incertidumbre e hipótesis refutadas deben coexistir en el mismo modelo de amenaza sin reducirse a una única historia causal.":"Positive findings, negative findings, uncertainty and refuted hypotheses must coexist in the same threat model without being flattened into a single causal story."}</div></section>
        </div>

        <section className={`${styles.card} ${styles.tableWrap}`}><h2>{isSpanish?"Resumen del corpus":"Corpus overview"}</h2><table className={styles.table}><thead><tr><th>{isSpanish?"Fecha":"Document date"}</th><th>{isSpanish?"Documento":"Document"}</th><th>{isSpanish?"Fuente":"Source"}</th><th>{isSpanish?"Rol de evidencia":"Evidence role"}</th><th>{isSpanish?"Contexto geográfico":"Geographic context"}</th></tr></thead><tbody>{mvHondiusBenchmark.documents.map((doc) => { const es=esDoc(doc.id) as {label:string;relation:string}; return <tr key={doc.id}><td>{doc.date}</td><td>{isSpanish?es.label:doc.label}</td><td>{doc.sourceLabel}</td><td>{isSpanish?es.relation:doc.relation}</td><td>{doc.location}</td></tr>; })}</tbody></table></section>
      </div>
    </DemoShell>
  );
}
