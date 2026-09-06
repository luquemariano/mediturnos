import { useEffect, useState } from "react";
import { LANDING_ASSETS } from "./landingConfig";
import { trackEvent } from "../analytics";
import "./ParaPsicopedagogosPage.css";

const problemas = [
  "Turnos coordinados por distintos medios",
  "Reprogramaciones difíciles de seguir",
  "Información de pacientes distribuida",
  "Evoluciones anteriores difíciles de consultar",
  "Horarios y disponibilidad gestionados manualmente",
  "Recordatorios dependientes de mensajes individuales",
] as const;

const funciones = [
  ["Agenda profesional", "Consultá próximos turnos, horarios y estados de atención desde una agenda clara."],
  ["Pacientes organizados", "Mantené tus pacientes y la información asociada en un mismo lugar."],
  ["Historia clínica y evoluciones", "Registrá evoluciones y consultá antecedentes previamente registrados."],
  ["Turnos y reprogramaciones", "Creá, consultá y reorganizá turnos según tu disponibilidad."],
  ["Horarios y disponibilidad", "Definí días, franjas horarias, excepciones y vacaciones."],
  ["Prestaciones y recordatorios", "Organizá prestaciones y enviá recordatorios automáticos por email."],
] as const;

const preguntas = [
  ["¿Qué puede organizar un psicopedagogo con Turnelia?", "Puede organizar turnos, pacientes, horarios, disponibilidad, prestaciones y el seguimiento de su práctica desde un solo lugar."],
  ["¿Puedo gestionar turnos?", "Sí. Podés crear, consultar y reprogramar turnos desde la agenda profesional."],
  ["¿Puedo registrar pacientes?", "Sí. Podés crear pacientes, buscarlos y acceder a la información asociada a su atención."],
  ["¿Puedo registrar evoluciones?", "Sí. Turnelia permite registrar evoluciones de la atención."],
  ["¿Puedo consultar la historia de un paciente?", "Sí. Podés consultar los antecedentes y evoluciones registrados previamente en su ficha."],
  ["¿Puedo definir mis horarios de atención?", "Sí. Podés configurar días, franjas horarias, excepciones y vacaciones."],
  ["¿Los pacientes reciben recordatorios?", "Sí. Turnelia envía recordatorios por email y permite confirmar o cancelar el turno desde ese mensaje."],
  ["¿Puedo usar Turnelia desde el celular?", "Sí. Podés acceder desde computadora, tablet o celular con conexión a Internet."],
  ["¿Necesito instalar un programa?", "No. Turnelia funciona desde el navegador."],
] as const;

function PsicopedagogosHeader() {
  const [abierto, setAbierto] = useState(false);
  return <header className="landing-header psicopedagogos-seo-header"><div className="landing-container landing-header__inner">
    <a className="landing-logo" href="/" aria-label="Turnelia, inicio"><img src="/brand/mediturnos-logo-horizontal.svg" alt="Turnelia" /></a>
    <button className="menu-button" type="button" aria-expanded={abierto} aria-controls="psicopedagogos-navigation" onClick={() => setAbierto(!abierto)}><span /><span /><span /><span className="sr-only">Abrir menú</span></button>
    <nav id="psicopedagogos-navigation" className={abierto ? "landing-nav is-open" : "landing-nav"} aria-label="Navegación principal" onClick={() => setAbierto(false)}><a href="#funciones">Funciones</a><a href="#como-empezar">Cómo empezar</a><a href="/ayuda">Centro de Ayuda</a><a className="nav-login" href="/login">Ingresar</a><a className="button button--small" href="/registro">Probar Turnelia</a></nav>
  </div></header>;
}

function PsicopedagogosFaq() {
  const [abierta, setAbierta] = useState<number | null>(null);
  return <section className="landing-section psicopedagogos-seo-faq"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Preguntas frecuentes</p><h2>Conocé cómo puede acompañarte Turnelia</h2></div><div className="faq__list">{preguntas.map(([pregunta, respuesta], index) => { const activa = abierta === index; const id = `psicopedagogos-faq-${index}`; return <div className={`faq__item${activa ? " is-open" : ""}`} key={pregunta}><h3><button type="button" aria-expanded={activa} aria-controls={id} onClick={() => setAbierta(activa ? null : index)}><span>{pregunta}</span><span className="faq__indicator" aria-hidden="true">{activa ? "−" : "+"}</span></button></h3><div id={id} className="faq__answer" hidden={!activa}><p>{respuesta}</p></div></div>; })}</div></div></section>;
}

function PsicopedagogosStructuredData() {
  useEffect(() => { const data = { "@context": "https://schema.org", "@graph": [
    { "@type": "WebPage", "@id": "https://turnelia.com.ar/para-psicopedagogos", "url": "https://turnelia.com.ar/para-psicopedagogos", "name": "Software para psicopedagogos | Turnelia", "description": "Organizá turnos, pacientes, horarios e historias clínicas con Turnelia. Un software simple para psicopedagogos que gestionan su práctica profesional." },
    { "@type": "SoftwareApplication", "name": "Turnelia", "applicationCategory": "BusinessApplication", "operatingSystem": "Web" },
    { "@type": "BreadcrumbList", "itemListElement": [{ "@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://turnelia.com.ar/" }, { "@type": "ListItem", "position": 2, "name": "Para psicopedagogos", "item": "https://turnelia.com.ar/para-psicopedagogos" }] },
    { "@type": "FAQPage", "mainEntity": preguntas.map(([name, text]) => ({ "@type": "Question", name, acceptedAnswer: { "@type": "Answer", text } })) },
  ] }; const script = document.createElement("script"); script.type = "application/ld+json"; script.textContent = JSON.stringify(data); document.head.append(script); return () => script.remove(); }, []);
  return null;
}

export default function ParaPsicopedagogosPage() {
  function medirRegistro(evento: React.MouseEvent<HTMLDivElement>) { if ((evento.target as Element).closest('a[href="/registro"]')) trackEvent("sign_up_click", { source: "psicopedagogos" }); }
  return <div className="landing-page psicopedagogos-seo" onClick={medirRegistro}><PsicopedagogosStructuredData /><PsicopedagogosHeader /><main>
    <section className="psicopedagogos-seo-hero"><div className="landing-container psicopedagogos-seo-hero__grid"><div><p className="eyebrow">Para psicopedagogos</p><h1>Software para psicopedagogos que simplifica tu gestión diaria</h1><p className="psicopedagogos-seo-hero__lead">Organizá turnos, pacientes, horarios y evoluciones desde un solo lugar. Turnelia te ayuda a mantener tu práctica ordenada sin depender de múltiples planillas, mensajes o anotaciones.</p><div className="button-row"><a className="button" href="/registro">Probar Turnelia</a><a className="button button--outline" href="#funciones">Ver cómo funciona</a></div></div><figure className="psicopedagogos-seo-hero__image"><img src={LANDING_ASSETS.dashboard} alt="Agenda profesional demo de Turnelia" loading="eager" fetchPriority="high" decoding="async" /></figure></div></section>
    <section className="psicopedagogos-seo-problems"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Problemas cotidianos</p><h2>Más orden para la gestión diaria de tu práctica</h2><p>Turnelia reúne las tareas habituales de tu agenda profesional en un mismo espacio.</p></div><div className="psicopedagogos-seo-problems__grid">{problemas.map(item => <article key={item}><span aria-hidden="true">✓</span><h3>{item}</h3></article>)}</div></div></section>
    <section id="funciones" className="landing-section psicopedagogos-seo-functions"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Funciones</p><h2>Una herramienta adecuada para organizar tu práctica profesional</h2></div><div className="features__grid">{funciones.map(([title, text]) => <article key={title}><h3>{title}</h3><p>{text}</p></article>)}</div></div></section>
    <section className="landing-section psicopedagogos-seo-showcase"><div className="landing-container psicopedagogos-seo-showcase__grid"><div><p className="eyebrow">Pacientes y evoluciones</p><h2>La información de cada paciente, organizada</h2><p>Accedé a la ficha de cada paciente, registrá evoluciones y consultá antecedentes previamente registrados para mantener el seguimiento asociado.</p><ul><li>Pacientes organizados y fáciles de encontrar</li><li>Historia clínica y evoluciones</li><li>Información asociada a cada paciente</li></ul></div><img src={LANDING_ASSETS.pacientes} alt="Ficha demo de pacientes de Turnelia" loading="lazy" /></div></section>
    <section className="landing-section psicopedagogos-seo-showcase psicopedagogos-seo-showcase--reverse"><div className="landing-container psicopedagogos-seo-showcase__grid"><div><p className="eyebrow">Turnos y agenda</p><h2>Organizá cada jornada con claridad</h2><p>Creá turnos, asociá pacientes y prestaciones, consultá los estados y reprogramá cuando cambien tus horarios o los de tus pacientes.</p><ul><li>Próximos turnos y horarios</li><li>Prestación y duración</li><li>Consulta y reprogramación</li></ul></div><img src={LANDING_ASSETS.dashboard} alt="Agenda demo de turnos de Turnelia" loading="lazy" /></div></section>
    <section className="landing-section psicopedagogos-seo-showcase"><div className="landing-container psicopedagogos-seo-showcase__grid"><div><p className="eyebrow">Disponibilidad y prestaciones</p><h2>Configurá la agenda según tu forma de trabajar</h2><p>Definí días, franjas horarias, excepciones y vacaciones. Organizá también tus prestaciones y sus duraciones para que tu disponibilidad represente tu actividad.</p></div><img src={LANDING_ASSETS.disponibilidad} alt="Disponibilidad demo de Turnelia" loading="lazy" /></div></section>
    <section className="landing-section psicopedagogos-seo-reminders"><div className="landing-container psicopedagogos-seo-reminders__grid"><div><p className="eyebrow">Recordatorios por email</p><h2>Ayudá a mantener actualizada tu agenda</h2><p>Turnelia envía un recordatorio automático por email antes del turno. El paciente puede confirmar o cancelar y el estado se actualiza en la agenda.</p></div><div className="psicopedagogos-seo-reminders__card"><strong>Recordatorio de turno</strong><span>Confirmación o cancelación desde el mismo email</span></div></div></section>
    <section className="landing-section psicopedagogos-seo-benefits"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Beneficios</p><h2>Una práctica más ordenada, desde cualquier dispositivo</h2></div><div className="psicopedagogos-seo-benefits__grid">{["Agenda más clara", "Información centralizada", "Menos herramientas separadas", "Seguimiento organizado", "Acceso desde distintos dispositivos"].map(item => <article key={item}><span>✓</span><strong>{item}</strong></article>)}</div></div></section>
    <section id="como-empezar" className="landing-section psicopedagogos-seo-steps"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Cómo empezar</p><h2>Comenzá a ordenar tu práctica en pocos pasos</h2></div><ol>{["Crear tu cuenta", "Configurar tu perfil", "Cargar tus prestaciones", "Definir tu disponibilidad", "Cargar pacientes y gestionar turnos"].map((item, index) => <li key={item}><span>{index + 1}</span><strong>{item}</strong></li>)}</ol></div></section>
    <PsicopedagogosFaq /><section className="dark-cta dark-cta--final"><div className="landing-container dark-cta__inner"><div><p className="eyebrow">Turnelia para tu práctica</p><h2>Organizá tu práctica profesional con Turnelia</h2><p>Empezá a gestionar pacientes, turnos y evoluciones desde un solo lugar.</p></div><a className="button button--light" href="/registro">Probar Turnelia</a></div></section>
  </main><footer className="landing-footer"><div className="landing-container psicopedagogos-seo-footer"><img src="/brand/mediturnos-logo-horizontal.svg" alt="Turnelia" /><div><a href="/">Inicio</a><a href="/software-para-consultorios">Gestión integral</a><a href="/sistema-de-turnos">Sistema de turnos</a><a href="/ayuda">Centro de Ayuda</a><a href="/registro">Probar Turnelia</a></div></div></footer></div>;
}
