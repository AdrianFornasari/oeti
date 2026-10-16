"use client";

import { useState } from "react";
import snapshot from "../data/mv-hondius.snapshot.json";

const names: Record<string, string> = {
  cluster: "Notificación del conglomerado", case_report: "Confirmación de un pasajero",
  laboratory_investigation: "Investigación de laboratorio", outbreak: "Actualización de casos",
  laboratory_result: "Identificación de la cepa Andes",
  human: "Humano", genomic: "Genómico", reported: "Reportado", confirmed: "Confirmado en el registro",
  pending: "Pendiente", active: "Activo", low: "Baja", none: "No registrada",
};
const label = (value: string) => names[value] ?? value;
const signals = snapshot.signals;
type Signal = (typeof signals)[number];
function date(value: string | null, time = false) {
  if (!value) return "No disponible";
  const parsed = new Date(value.length === 10 ? `${value}T12:00:00Z` : value.replace(" ", "T"));
  return new Intl.DateTimeFormat("es-AR", {
    day: "2-digit", month: "short", year: "numeric", timeZone: "America/Argentina/Buenos_Aires",
    ...(time ? { hour: "2-digit", minute: "2-digit" } as const : {}),
  }).format(parsed);
}
function Evidence({ signal }: { signal: Signal }) {
  const excerpts = snapshot.evidence.filter(item => item.signal_id === signal.id);
  return <div className="evidence-list">{excerpts.length ? excerpts.map((item, index) =>
    <figure key={item.id}>
      <figcaption>Fragmento {index + 1} · evidencia literal</figcaption>
      <blockquote>{item.excerpt}</blockquote>
      <div className="locator">{item.page_number ? `Página ${item.page_number}` : "Página no registrada"}
        {item.document_locator ? ` · ${item.document_locator}` : " · ubicación del fragmento no registrada"}</div>
    </figure>) : <p>No hay fragmentos disponibles para esta señal.</p>}</div>;
}

export default function HomePage() {
  const [selectedId, setSelectedId] = useState(signals[0].id);
  const selected = signals.find(signal => signal.id === selectedId)!;
  const membership = snapshot.memberships.find(item => item.signal_id === selectedId)!;
  const related = snapshot.relations.filter(item => item.source_signal_id === selectedId || item.target_signal_id === selectedId);
  const documents = [...new Set(signals.map(signal => signal.raw_item_id))].map(id => signals.filter(signal => signal.raw_item_id === id));
  function revealSignal(id: string) {
    setSelectedId(id);
    document.getElementById("detalle")?.scrollIntoView({ behavior: "smooth", block: "start" });
    document.getElementById("selected-heading")?.focus({ preventScroll: true });
  }
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(snapshot, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url; anchor.download = "oeti-mv-hondius-snapshot.json"; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <>
    <header className="topbar">
      <a className="brand" href="#inicio" aria-label="OETI, inicio"><span className="brand-mark">O</span> OETI <span className="brand-sub">Inteligencia epidemiológica</span></a>
      <span className="local-badge"><span /> Demo local · solo lectura</span>
    </header>
    <div className="workspace">
      <aside className="sidebar" aria-label="Navegación de la ficha">
        <p className="eyebrow">CASO DE DESARROLLO</p>
        <a className="side-active" href="#inicio">Ficha del evento <span>01</span></a>
        <a href="#cronologia">Publicaciones y señales <span>02</span></a>
        <a href="#relaciones">Relaciones <span>03</span></a>
        <a href="#procedencia">Procedencia <span>04</span></a>
        <div className="side-note"><span className="small-dot" /> Datos congelados<p>Reconstrucción retrospectiva. Sin monitoreo ni alertas en vivo.</p></div>
      </aside>
      <main id="inicio">
        <div className="breadcrumb">Eventos <span>/</span> MV Hondius</div>
        <section className="hero" aria-labelledby="event-title">
          <div><p className="eyebrow">FICHA DE EVIDENCIA · HANTAVIRUS</p><h1 id="event-title">MV Hondius</h1>
            <p className="hero-description">De la publicación al evento.{" "}<br />Un recorrido por la evidencia registrada.</p>
            <div className="hero-tags"><span>Humano</span><span>Genómico</span><span className="amber">Revisión pendiente</span></div>
          </div>
          <div className="hero-meta"><span className="eyebrow">CAPTURA DEL SNAPSHOT</span><strong>{date(snapshot.captured_at)}</strong><span>{date(snapshot.captured_at, true)} · hora argentina</span>
            <div className="hero-actions"><button onClick={() => window.print()}>Imprimir ficha</button><button className="secondary" onClick={download}>Descargar datos</button></div>
          </div>
        </section>
        <div className="context-note"><strong>Lectura retrospectiva.</strong> Esta ficha muestra registros capturados en una transacción de solo lectura. Las señales siguen pendientes de revisión; el caso no demuestra vigilancia prospectiva ni generalización.</div>
        <section className="metrics" aria-label="Resumen del evento">
          <div><span>Señales vinculadas</span><strong>{signals.length.toString().padStart(2, "0")}</strong><small>Cinco membresías al evento</small></div>
          <div><span>Relaciones entre señales</span><strong>{snapshot.relations.length.toString().padStart(2, "0")}</strong><small>Registradas como refinamientos</small></div>
          <div><span>Publicaciones de origen</span><strong>{documents.length.toString().padStart(2, "0")}</strong><small>{snapshot.evidence.length} fragmentos literales</small></div>
          <div><span>Confianza del evento</span><strong className="confidence">{label(snapshot.event.evidence_confidence)}</strong><small>Valor del registro · prioridad {snapshot.event.priority}</small></div>
        </section>
        <section className="event-facts" aria-label="Estado registrado">
          <div><span>Inicio registrado del evento</span><strong>{date(snapshot.event.event_start_date)}</strong></div>
          <div><span>Estado al capturar</span><strong>{label(snapshot.event.lifecycle_status)}</strong></div>
          <div><span>Convergencia entre sectores</span><strong>{label(snapshot.event.cross_sector_convergence)}</strong></div>
          <p>Los dominios humano y genómico no acreditan convergencia independiente entre sectores. La prioridad P3 es un valor almacenado, sin validación de calibración en esta demo.</p>
        </section>
        <section id="cronologia" className="section-header"><div><p className="eyebrow">01 / RECORRIDO DOCUMENTAL</p><h2>Publicaciones y señales</h2></div><p>Seleccioná una señal para ver su evidencia.</p></section>
        <div className="trace-grid">
          <section className="timeline" aria-label="Cronología por fecha de publicación">
            <p className="timeline-label">Orden por publicación · no por fecha del hecho</p>
            {documents.map((group, index) => <article className="publication" key={group[0].raw_item_id}>
              <div className="publication-date"><span className="timeline-node">{index + 1}</span><time>{date(group[0].published_at)}</time><span>PUBLICACIÓN</span></div>
              <h3><a href={group[0].source_url} target="_blank" rel="noreferrer">{group[0].source_title} <span aria-label="Abrir fuente">↗</span></a></h3>
              <div className="signal-list">{group.map(signal => <button key={signal.id} className={`signal-button ${signal.id === selectedId ? "selected" : ""}`} aria-pressed={signal.id === selectedId} onClick={() => setSelectedId(signal.id)}>
                <span className="signal-number">S{signals.indexOf(signal) + 1}</span><span><strong>{label(signal.signal_type)}</strong><small>{signal.domains.map(label).join(" · ")}</small></span><span className="select-arrow" aria-hidden="true">→</span>
              </button>)}</div>
            </article>)}
          </section>
          <section id="detalle" className="inspector" aria-labelledby="selected-heading">
            <div className="inspector-top"><span className="eyebrow">SEÑAL S{signals.indexOf(selected) + 1}</span><span className="status-pill">Revisión: {label(selected.review_status)}</span></div>
            <div aria-live="polite" aria-atomic="true"><h2 id="selected-heading" tabIndex={-1}>{label(selected.signal_type)}</h2><p className="signal-summary">{selected.summary}</p></div>
            <dl className="signal-facts"><div><dt>Fecha del hecho registrada</dt><dd>{date(selected.occurred_start)}{selected.occurred_end ? ` – ${date(selected.occurred_end)}` : ""}</dd></div><div><dt>Estado de verificación</dt><dd>{label(selected.verification_status)}</dd></div></dl>
            {selected.signal_type === "outbreak" && <p className="evidence-note">La cita distingue seis confirmados y dos probables dentro de los ocho casos. El resumen y el estado de verificación se conservan como están registrados.</p>}
            <div className="evidence-heading"><h3>Evidencia que respalda la señal</h3><span>FUENTE ORIGINAL</span></div>
            <Evidence signal={selected} />
            <a className="source-link" href={selected.source_url} target="_blank" rel="noreferrer">Leer la publicación original ↗</a>
            <div className="membership"><span className="eyebrow">VÍNCULO CON EL EVENTO</span><p>Esta señal apoya el evento MV Hondius.</p><small>Decisión registrada: {membership.match_decision} · relación: {membership.relation_to_event}. Puntaje de membresía: {membership.match_score ?? "no disponible"}.</small></div>
            <details className="technical"><summary>Identificadores y extracción</summary><dl><dt>Señal</dt><dd>{selected.id}</dd><dt>Documento</dt><dd>{selected.raw_item_id}</dd><dt>Extractor / modelo histórico</dt><dd>{selected.extractor_version ?? "No disponible"} / {selected.model_name ?? "No disponible"}</dd><dt>Precisión temporal</dt><dd>{selected.date_precision}</dd></dl></details>
          </section>
        </div>
        <section id="relaciones" className="relations-section">
          <div className="section-header"><div><p className="eyebrow">02 / CONTINUIDAD DE EVIDENCIA</p><h2>Relaciones registradas</h2></div><p>{related.length} de las 3 involucran la señal seleccionada.</p></div>
          <p className="section-description">La flecha conserva origen y destino almacenados. <code>refines</code> indica refinamiento; los puntajes del matcher no son probabilidades de vínculo epidemiológico.</p>
          <div className="relation-list">{snapshot.relations.map(relation => {
            const source = signals.find(signal => signal.id === relation.source_signal_id)!;
            const target = signals.find(signal => signal.id === relation.target_signal_id)!;
            return <article key={relation.id} className={`relation-row ${related.includes(relation) ? "involved" : ""}`}>
              <button onClick={() => revealSignal(source.id)}>S{signals.indexOf(source) + 1} · {label(source.signal_type)}</button><span className="relation-arrow">→ <small>{relation.relation}</small></span><button onClick={() => revealSignal(target.id)}>S{signals.indexOf(target) + 1} · {label(target.signal_type)}</button><span className="relation-score">Puntaje <strong>{relation.score ?? "No disponible"}</strong></span>
              <details><summary>Registro de relación</summary><p>ID: {relation.id} · matcher {relation.matcher_version ?? "no disponible"} · conflicto fuerte: {relation.hard_conflict ? "sí" : "no"}.</p></details>
            </article>;
          })}</div>
        </section>
        <section id="procedencia" className="provenance">
          <div><p className="eyebrow">03 / PROCEDENCIA Y LÍMITES</p><h2>Una ficha que permite volver a la fuente</h2><p>Las citas son fragmentos conservados en la base. No se registraron páginas ni posiciones para estos fragmentos; su coincidencia con las publicaciones actuales no fue revalidada en esta captura.</p></div>
          <dl><div><dt>Captura de datos</dt><dd>{date(snapshot.captured_at, true)} · Argentina</dd></div><div><dt>Origen</dt><dd>Eventos, membresías, señales, relaciones y evidencia persistidos</dd></div><div><dt>Modo</dt><dd>Snapshot congelado · READ ONLY / REPEATABLE READ</dd></div><div><dt>Revisión del evento</dt><dd>{label(snapshot.event.review_status)}</dd></div></dl>
          <details><summary>Ver trazabilidad técnica completa</summary><dl><dt>Evento</dt><dd>{snapshot.event.id}</dd><dt>Código</dt><dd>{snapshot.event.event_code}</dd><dt>Título original</dt><dd>{snapshot.event.title}</dd><dt>Base integrada de la implementación</dt><dd>{snapshot.implementation_base}</dd><dt>Commit de las extracciones históricas</dt><dd>No disponible en los registros. La base de implementación no identifica esas extracciones.</dd><dt>Versiones históricas</dt><dd>Los modelos y extractores figuran por señal; no se sustituyen por el default actual del worker.</dd></dl><p>La fecha first_signal_at almacenada ({date(snapshot.event.first_signal_at, true)}) coincide con una publicación; no se usa como primera detección prospectiva ni para medir anticipación.</p></details>
        </section>
        <section className="print-evidence"><h2>Todas las señales y su evidencia</h2><p className="print-url">Evento: {snapshot.event.id}<br />Base de implementación: {snapshot.implementation_base}<br />Commit de extracciones históricas: no disponible.</p>{signals.map(signal => <article key={signal.id}><h3>S{signals.indexOf(signal) + 1} · {label(signal.signal_type)}</h3><p>{signal.summary}</p><p>Publicación: {date(signal.published_at)} · Fecha del hecho: {date(signal.occurred_start)} · Revisión: {label(signal.review_status)}</p><Evidence signal={signal} /><p className="print-url">Fuente: <a href={signal.source_url} target="_blank" rel="noreferrer">{signal.source_url}</a></p><small>ID: {signal.id} · Extractor: {signal.extractor_version ?? "No disponible"} · Modelo: {signal.model_name ?? "No disponible"}</small></article>)}</section>
        <footer>OETI <span>Argentina · evidencia antes de decisión</span><span>Demo retrospectiva · sin acciones de escritura</span></footer>
      </main>
    </div>
  </>;
}
