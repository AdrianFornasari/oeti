"use client";

import Link from "next/link";
import { DemoShell, PrototypeNote } from "../demo-shell";
import { useDemoPreferences } from "../demo-preferences";
import styles from "../demo.module.css";

export default function PresentationGuidePage() {
  const { isSpanish } = useDemoPreferences();

  const steps = isSpanish ? [
    {
      n: "1",
      time: "1–2 min",
      title: "Panel ejecutivo",
      href: "/demo",
      action: "Mostrar el alcance futuro de OETI y distinguir inmediatamente los datos ilustrativos del caso real.",
      message: "OETI integra señales de salud humana, animal y ambiental en una misma plataforma, pero esta demo no pretende simular una operación real completa: el caso MV Hondius sí está basado en evidencia adjudicada.",
      focus: "Señalar el rótulo DATOS ILUSTRATIVOS y luego abrir Caso real MV Hondius.",
    },
    {
      n: "2",
      time: "2 min",
      title: "Explorador de amenazas — MV Hondius",
      href: "/demo/threats/hantavirus",
      action: "Recorrer la cronología y mostrar cómo OETI conserva hechos positivos, negativos e incertidumbre.",
      message: "El sistema no fuerza una única explicación. Mantiene cada documento, su contexto temporal y geográfico y el rol que cumple dentro de la investigación.",
      focus: "Señalar 11 casos identificados, 9 confirmados y las dos investigaciones con evidencia negativa.",
    },
    {
      n: "3",
      time: "2 min",
      title: "Convergencia One Health",
      href: "/demo/threats/hantavirus/one-health",
      action: "Mostrar cómo convergen salud humana, fauna, genómica y movilidad sin convertir la convergencia en causalidad.",
      message: "El valor One Health está en reconciliar dominios distintos. Fauna seropositiva, similitud genómica o antecedente de viaje pueden aportar contexto sin demostrar por sí solos el origen del brote.",
      focus: "Destacar Wildlife → Human: refutado para los roedores analizados, y ausencia de señal ambiental adjudicada.",
    },
    {
      n: "4",
      time: "1–2 min",
      title: "Detalle de señal ASM-01",
      href: "/demo/signals/asm-01",
      action: "Bajar desde el nivel de amenaza hasta una señal concreta y verificable.",
      message: "OETI convierte evidencia documental en señales estructuradas, pero conserva siempre el texto fuente y los límites de interpretación.",
      focus: "Mostrar 5 Abrothrix seropositivos, Ushuaia, fecha documental y el límite causal explícito.",
    },
    {
      n: "5",
      time: "1–2 min",
      title: "Trazabilidad de evidencia",
      href: "/demo/evidence/asm-01",
      action: "Mostrar el recorrido completo desde la fuente hasta el uso operativo.",
      message: "Nada se pierde: fuente, afirmaciones extraídas, señal automática y decisión humana permanecen separadas y auditables.",
      focus: "Recorrer visualmente los cinco pasos de izquierda a derecha.",
    },
    {
      n: "6",
      time: "2 min",
      title: "Revisión del analista",
      href: "/demo/review/asm-01",
      action: "Demostrar la supervisión humana confirmando, corrigiendo o rechazando una señal.",
      message: "La máquina propone; la evidencia se conserva; el analista decide. Una corrección o rechazo no reescribe retrospectivamente la fuente.",
      focus: "Para una demo fluida, usar Confirmar. Reservar Corregir/Rechazar para preguntas o una segunda pasada.",
    },
    {
      n: "7",
      time: "2 min",
      title: "Evaluación del sistema",
      href: "/demo/evaluation",
      action: "Cerrar mostrando que OETI mide su propio desempeño contra un corpus adjudicado.",
      message: "La plataforma no solo produce inteligencia: también cuantifica cuándo todavía no es suficientemente confiable para habilitar la siguiente etapa automática.",
      focus: "Mostrar cobertura 6/6, recall 0.90, 14 señales de más y el vinculador de eventos todavía deshabilitado.",
    },
  ] : [
    {
      n: "1", time: "1–2 min", title: "Executive dashboard", href: "/demo",
      action: "Show OETI's future operating scope and immediately distinguish illustrative data from the real case.",
      message: "OETI integrates human, animal and environmental health signals in one platform. This demo does not pretend to be a complete live operation: the MV Hondius case is grounded in adjudicated evidence.",
      focus: "Point out ILLUSTRATIVE DATA, then open the real MV Hondius case.",
    },
    {
      n: "2", time: "2 min", title: "Threat Explorer — MV Hondius", href: "/demo/threats/hantavirus",
      action: "Walk through the timeline and show how OETI preserves positive, negative and uncertain evidence.",
      message: "The system does not force a single explanation. It preserves each document, its temporal and geographic context and its role in the investigation.",
      focus: "Point out 11 identified cases, 9 confirmed cases and two negative-evidence investigations.",
    },
    {
      n: "3", time: "2 min", title: "One Health convergence", href: "/demo/threats/hantavirus/one-health",
      action: "Show how human health, wildlife, genomics and mobility converge without turning convergence into causality.",
      message: "One Health value lies in reconciling distinct domains. Seropositive wildlife, genomic similarity or travel history may add context without proving outbreak origin.",
      focus: "Highlight Wildlife → Human as refuted for the analysed rodents, and the absence of adjudicated environmental evidence.",
    },
    {
      n: "4", time: "1–2 min", title: "ASM-01 signal detail", href: "/demo/signals/asm-01",
      action: "Move from threat level to one concrete, verifiable signal.",
      message: "OETI turns documentary evidence into structured signals while preserving source text and interpretation limits.",
      focus: "Show 5 seropositive Abrothrix rodents, Ushuaia, document date and the explicit causal limit.",
    },
    {
      n: "5", time: "1–2 min", title: "Evidence traceability", href: "/demo/evidence/asm-01",
      action: "Show the full path from source to operational use.",
      message: "Nothing is lost: source, extracted claims, machine signal and human decision remain separate and auditable.",
      focus: "Walk through the five steps from left to right.",
    },
    {
      n: "6", time: "2 min", title: "Analyst review", href: "/demo/review/asm-01",
      action: "Demonstrate human oversight by confirming, correcting or rejecting a signal.",
      message: "The machine proposes; evidence is preserved; the analyst decides. A correction or rejection does not retrospectively rewrite the source.",
      focus: "For a smooth demo, use Confirm. Reserve Correct/Reject for questions or a second pass.",
    },
    {
      n: "7", time: "2 min", title: "System evaluation", href: "/demo/evaluation",
      action: "Close by showing that OETI measures its own performance against an adjudicated corpus.",
      message: "The platform does not only produce intelligence: it also quantifies when it is not yet reliable enough to enable the next automated stage.",
      focus: "Show 6/6 coverage, 0.90 recall, 14 extra signals and the event matcher still disabled.",
    },
  ];

  return (
    <DemoShell active="dashboard">
      <div className={styles.content}>
        <PrototypeNote>{isSpanish
          ? "Guía interna de presentación — no forma parte del flujo operativo de OETI. Está pensada para ensayar y conducir una demo de 10–15 minutos sin perder el hilo narrativo."
          : "Internal presentation guide — this is not part of OETI's operational workflow. It is designed to rehearse and conduct a 10–15 minute demo without losing the narrative thread."}</PrototypeNote>

        <div className={styles.pageHead}>
          <div>
            <div className={styles.breadcrumb}><Link href="/demo">Dashboard</Link> › {isSpanish ? "Modo presentación" : "Presentation mode"}</div>
            <h1>{isSpanish ? "Ruta guiada para sponsor" : "Guided sponsor route"}</h1>
            <p className={styles.subtitle}>{isSpanish ? "Duración objetivo: 12–14 minutos · Caso conductor: MV Hondius · Cierre: evaluación objetiva del sistema" : "Target duration: 12–14 minutes · Lead case: MV Hondius · Close: objective system evaluation"}</p>
          </div>
          <div className={styles.actions}><Link className={`${styles.button} ${styles.buttonPrimary}`} href="/demo">{isSpanish ? "Comenzar presentación →" : "Start presentation →"}</Link></div>
        </div>

        <section className={styles.card} style={{ marginBottom: 14 }}>
          <h2>{isSpanish ? "Mensaje central" : "Core message"}</h2>
          <div className={styles.detailPanel}>{isSpanish
            ? "OETI integra evidencia One Health, transforma documentos en señales trazables, mantiene la incertidumbre y la evidencia negativa, incorpora revisión humana y evalúa objetivamente cuándo su automatización es suficientemente confiable."
            : "OETI integrates One Health evidence, transforms documents into traceable signals, preserves uncertainty and negative evidence, incorporates human review and objectively evaluates when its automation is reliable enough."}</div>
        </section>

        <div style={{ display: "grid", gap: 12 }}>
          {steps.map((step) => (
            <section className={styles.card} key={step.n}>
              <div className={styles.pageHead} style={{ marginBottom: 8 }}>
                <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                  <div className={`${styles.metricIcon} ${styles.blue}`}>{step.n}</div>
                  <div><h2 style={{ marginBottom: 4 }}>{step.title}</h2><div className={`${styles.small} ${styles.muted}`}>{step.time}</div></div>
                </div>
                <Link className={styles.button} href={step.href}>{isSpanish ? "Abrir pantalla →" : "Open screen →"}</Link>
              </div>
              <div className={styles.summaryList}>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Qué hacer" : "What to do"}</div><div>{step.action}</div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Mensaje" : "Message"}</div><div><strong>{step.message}</strong></div></div>
                <div className={styles.summaryRow}><div className={styles.summaryKey}>{isSpanish ? "Señalar" : "Point out"}</div><div>{step.focus}</div></div>
              </div>
            </section>
          ))}
        </div>

        <section className={styles.card} style={{ marginTop: 14 }}>
          <h2>{isSpanish ? "Antes de presentar" : "Before presenting"}</h2>
          <ul className={styles.insights}>
            <li>{isSpanish ? "Usar español y modo claro salvo que el contexto de la sala justifique otra opción." : "Use Spanish and light mode unless the room context calls for another choice."}</li>
            <li>{isSpanish ? "Comprobar que /demo carga y que la navegación móvil/PC funciona antes de comenzar." : "Verify that /demo loads and that desktop/mobile navigation works before starting."}</li>
            <li>{isSpanish ? "Restablecer el estado de revisión de ASM-01 si querés demostrar el paso de Pendiente → Confirmada durante la presentación." : "Reset ASM-01 review state if you want to demonstrate Pending → Confirmed during the presentation."}</li>
            <li>{isSpanish ? "No dedicar tiempo a explicar nombres internos como signal_role, arquitectura v0.4.4 o rutas de archivos salvo que te lo pregunten." : "Do not spend time explaining internal names such as signal_role, architecture v0.4.4 or file paths unless asked."}</li>
            <li>{isSpanish ? "Cerrar en Evaluation: transmite que OETI conoce sus límites y no habilita automatización adicional cuando los criterios aún no se cumplen." : "Close on Evaluation: it shows that OETI knows its limits and does not enable further automation while criteria are unmet."}</li>
          </ul>
        </section>
      </div>
    </DemoShell>
  );
}
