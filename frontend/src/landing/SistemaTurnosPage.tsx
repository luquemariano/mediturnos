import { useEffect, useState } from "react";
import { LANDING_ASSETS } from "./landingConfig";
import { trackEvent } from "../analytics";
import "./SistemaTurnosPage.css";

const problemas = [
  "Turnos repartidos entre WhatsApp, papel o planillas",
  "Cambios de horario difíciles de seguir",
  "Reprogramaciones manuales y disponibilidad desactualizada",
  "Dificultad para saber cómo queda organizada la jornada",
  "Pacientes que no confirman su asistencia",
] as const;

const funciones = [
  ["Agenda profesional", "Revisá próximos turnos, horarios y estados de atención desde una vista clara."],
  ["Crear turnos", "Asociá un paciente, elegí la prestación y definí fecha y hora."],
  ["Reprogramar", "Actualizá los turnos cuando cambien tus horarios o los de tus pacientes."],
  ["Disponibilidad", "Configurá días, franjas horarias, excepciones y vacaciones."],
  ["Prestaciones", "Organizá servicios y duraciones para ordenar mejor tu tiempo."],
  ["Recordatorios por email", "Tus pacientes pueden confirmar o cancelar desde el email recibido."],
] as const;

const preguntas = [
  ["¿Qué es un sistema de turnos para consultorios?", "Es una herramienta para organizar en un solo lugar la agenda, los horarios, la disponibilidad y los turnos de un consultorio."],
  ["¿Puedo crear y reprogramar turnos?", "Sí. Podés crear turnos asociando un paciente y una prestación, y actualizar la fecha u horario cuando sea necesario."],
  ["¿Puedo definir mis horarios de atención?", "Sí. Turnelia permite configurar tus días y franjas horarias de atención."],
  ["¿Puedo configurar días no laborables o vacaciones?", "Sí. Podés agregar excepciones y vacaciones para que la disponibilidad refleje tu agenda real."],
  ["¿Puedo usar diferentes prestaciones?", "Sí. Podés configurar las prestaciones de tu actividad y sus duraciones para organizar los turnos."],
  ["¿Los pacientes reciben recordatorios?", "Sí. Turnelia envía recordatorios automáticos por email antes del turno, con opciones para confirmar o cancelar."],
  ["¿Puedo usar Turnelia desde el celular?", "Sí. La agenda puede consultarse desde computadora, tablet o celular con conexión a Internet."],
  ["¿Necesito instalar un programa?", "No. Turnelia funciona desde el navegador."],
  ["¿Turnelia sirve para profesionales independientes?", "Sí. Es una opción para profesionales que gestionan sus propios turnos, pacientes y horarios."],
] as const;

function TurnosHeader() {
  const [abierto, setAbierto] = useState(false);
  return <header className="landing-header turnos-seo-header"><div className="landing-container landing-header__inner">
    <a className="landing-logo" href="/" aria-label="Turnelia, inicio"><img src="/brand/mediturnos-logo-horizontal.svg" alt="Turnelia" /></a>
    <button className="menu-button" type="button" aria-expanded={abierto} aria-controls="turnos-navigation" onClick={() => setAbierto(!abierto)}><span /><span /><span /><span className="sr-only">Abrir menú</span></button>
    <nav id="turnos-navigation" className={abierto ? "landing-nav is-open" : "landing-nav"} aria-label="Navegación principal" onClick={() => setAbierto(false)}><a href="#funciones">Funciones</a><a href="#como-empezar">Cómo empezar</a><a href="/software-para-consultorios">Gestión integral</a><a href="/ayuda">Centro de Ayuda</a><a className="nav-login" href="/login">Ingresar</a><a className="button button--small" href="/registro">Probar Turnelia</a></nav>
  </div></header>;
}

function TurnosFaq() {
  const [abierta, setAbierta] = useState<number | null>(null);
  return <section className="landing-section turnos-seo-faq"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Preguntas frecuentes</p><h2>Respuestas sobre tu agenda de turnos</h2></div><div className="faq__list">{preguntas.map(([pregunta, respuesta], index) => { const activa = abierta === index; const id = `turnos-faq-${index}`; return <div className={`faq__item${activa ? " is-open" : ""}`} key={pregunta}><h3><button type="button" aria-expanded={activa} aria-controls={id} onClick={() => setAbierta(activa ? null : index)}><span>{pregunta}</span><span className="faq__indicator" aria-hidden="true">{activa ? "−" : "+"}</span></button></h3><div id={id} className="faq__answer" hidden={!activa}><p>{respuesta}</p></div></div>; })}</div></div></section>;
}

function TurnosStructuredData() {
  useEffect(() => { const data = { "@context": "https://schema.org", "@graph": [
    { "@type": "WebPage", "@id": "https://turnelia.com.ar/sistema-de-turnos", "url": "https://turnelia.com.ar/sistema-de-turnos", "name": "Sistema de turnos para consultorios | Turnelia", "description": "Organizá turnos, horarios y disponibilidad desde una agenda simple. Creá, reprogramá y gestioná citas con Turnelia." },
    { "@type": "SoftwareApplication", "name": "Turnelia", "applicationCategory": "BusinessApplication", "operatingSystem": "Web" },
    { "@type": "BreadcrumbList", "itemListElement": [{ "@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://turnelia.com.ar/" }, { "@type": "ListItem", "position": 2, "name": "Sistema de turnos", "item": "https://turnelia.com.ar/sistema-de-turnos" }] },
    { "@type": "FAQPage", "mainEntity": preguntas.map(([name, text]) => ({ "@type": "Question", name, acceptedAnswer: { "@type": "Answer", text } })) },
  ] }; const script = document.createElement("script"); script.type = "application/ld+json"; script.textContent = JSON.stringify(data); document.head.append(script); return () => script.remove(); }, []);
  return null;
}

export default function SistemaTurnosPage() {
  function medirRegistro(evento: React.MouseEvent<HTMLDivElement>) { if ((evento.target as Element).closest('a[href="/registro"]')) trackEvent("sign_up_click", { source: "sistema_turnos" }); }
  return <div className="landing-page turnos-seo" onClick={medirRegistro}><TurnosStructuredData /><TurnosHeader /><main>
    <section className="turnos-seo-hero"><div className="landing-container turnos-seo-hero__grid"><div><p className="eyebrow">Agenda profesional</p><h1>Sistema de turnos para organizar tu agenda profesional</h1><p className="turnos-seo-hero__lead">Centralizá tus turnos, horarios y disponibilidad en una agenda clara. Con Turnelia podés organizar cada jornada, reprogramar citas y mantener actualizado el estado de cada atención.</p><div className="button-row"><a className="button" href="/registro">Probar Turnelia</a><a className="button button--outline" href="#funciones">Ver cómo funciona</a></div></div><figure className="turnos-seo-hero__image"><img src={LANDING_ASSETS.dashboard} alt="Agenda de turnos de Turnelia" loading="eager" fetchPriority="high" decoding="async" /></figure></div></section>
    <section className="turnos-seo-problem"><div className="landing-container"><div className="section-heading"><p className="eyebrow">El problema</p><h2>Cuando organizar turnos se vuelve una tarea más</h2><p>Una agenda centralizada ayuda a tener una visión más clara de cada jornada.</p></div><div className="turnos-seo-problem__grid">{problemas.map(item => <article key={item}><span aria-hidden="true">✓</span><h3>{item}</h3></article>)}</div></div></section>
    <section id="funciones" className="landing-section turnos-seo-functions"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Funciones para tu agenda</p><h2>Todo lo que necesitás para gestionar turnos</h2></div><div className="features__grid">{funciones.map(([title, text]) => <article key={title}><h3>{title}</h3><p>{text}</p></article>)}</div></div></section>
    <section className="landing-section turnos-seo-showcase"><div className="landing-container turnos-seo-showcase__grid"><div><p className="eyebrow">Agenda profesional</p><h2>Tu jornada, ordenada desde el primer vistazo</h2><p>Consultá próximos turnos, horarios y estados de atención desde una agenda pensada para acompañar tu trabajo diario.</p><ul><li>Vista de agenda y próximos turnos</li><li>Estados de cada atención</li><li>Acceso rápido a la información necesaria</li></ul></div><img src={LANDING_ASSETS.dashboard} alt="Vista demo de agenda profesional" loading="lazy" /></div></section>
    <section className="landing-section turnos-seo-showcase turnos-seo-showcase--reverse"><div className="landing-container turnos-seo-showcase__grid"><div><p className="eyebrow">Crear y gestionar turnos</p><h2>Cada turno con la información necesaria</h2><p>Asociá un paciente, seleccioná una prestación y definí la fecha y hora. Después podés consultar el estado de cada atención desde la agenda.</p><ul><li>Paciente asociado</li><li>Prestación y duración</li><li>Fecha, horario y estado</li></ul></div><img src={LANDING_ASSETS.pacientes} alt="Paciente demo relacionado con un turno" loading="lazy" /></div></section>
    <section className="landing-section turnos-seo-showcase"><div className="landing-container turnos-seo-showcase__grid"><div><p className="eyebrow">Horarios y disponibilidad</p><h2>Configurá cuándo atendés</h2><p>Definí tus días de atención, franjas horarias, excepciones y vacaciones para que la disponibilidad profesional acompañe tu agenda real.</p><ul><li>Días y franjas horarias</li><li>Excepciones y vacaciones</li><li>Disponibilidad centralizada</li></ul></div><img src={LANDING_ASSETS.disponibilidad} alt="Configuración demo de disponibilidad" loading="lazy" /></div></section>
    <section className="landing-section turnos-seo-reminders"><div className="landing-container turnos-seo-reminders__grid"><div><p className="eyebrow">Recordatorios de turnos</p><h2>Una agenda más actualizada</h2><p>Turnelia envía un recordatorio automático por email antes del turno. El paciente puede confirmar o cancelar, y el estado se actualiza en la agenda.</p></div><div className="turnos-seo-reminders__card"><strong>Recordatorio por email</strong><span>Confirmación o cancelación desde el mismo mensaje</span></div></div></section>
    <section className="landing-section turnos-seo-benefits"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Beneficios</p><h2>Más claridad para cada jornada</h2></div><div className="turnos-seo-benefits__grid">{["Agenda más clara", "Menos tareas dispersas", "Reprogramaciones más ordenadas", "Disponibilidad centralizada", "Seguimiento simple de cada jornada"].map(item => <article key={item}><span>✓</span><strong>{item}</strong></article>)}</div></div></section>
    <section id="como-empezar" className="landing-section turnos-seo-steps"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Cómo empezar</p><h2>Configurá tu agenda en pocos pasos</h2></div><ol>{["Crear tu cuenta", "Configurar prestaciones", "Definir disponibilidad", "Cargar pacientes", "Crear el primer turno"].map((item, index) => <li key={item}><span>{index + 1}</span><strong>{item}</strong></li>)}</ol></div></section>
    <TurnosFaq /><section className="dark-cta dark-cta--final"><div className="landing-container dark-cta__inner"><div><p className="eyebrow">Turnelia</p><h2>Ordená tus turnos con Turnelia</h2><p>Empezá a gestionar tu agenda profesional desde un solo lugar.</p></div><a className="button button--light" href="/registro">Probar Turnelia</a></div></section>
  </main><footer className="landing-footer"><div className="landing-container turnos-seo-footer"><img src="/brand/mediturnos-logo-horizontal.svg" alt="Turnelia" /><div><a href="/">Inicio</a><a href="/software-para-consultorios">Gestión integral</a><a href="/ayuda">Centro de Ayuda</a><a href="/registro">Probar Turnelia</a></div></div></footer></div>;
}
