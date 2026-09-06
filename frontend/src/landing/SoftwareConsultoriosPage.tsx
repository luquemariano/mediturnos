import { useEffect, useState } from "react";
import { LANDING_ASSETS } from "./landingConfig";
import { trackEvent } from "../analytics";
import "./SoftwareConsultoriosPage.css";

const funciones = [
  ["Agenda profesional", "Visualizá tu jornada y los próximos turnos de un vistazo."],
  ["Pacientes", "Buscá pacientes y accedé a su ficha para organizar la atención."],
  ["Disponibilidad", "Definí días, franjas horarias, excepciones y vacaciones."],
  ["Prestaciones", "Configurá los servicios que ofrecés y su duración."],
  ["Recordatorios por email", "Ayudá a tus pacientes a confirmar o cancelar sus turnos."],
  ["Seguimiento de la atención", "Registrá evoluciones y consultá el seguimiento cuando lo necesites."],
] as const;

const preguntas = [
  ["¿Qué es un software para consultorios?", "Es una herramienta que reúne en un mismo lugar la agenda, los turnos, los pacientes y la información necesaria para organizar la actividad diaria de un consultorio."],
  ["¿Turnelia sirve para profesionales independientes?", "Sí. Turnelia está pensado para profesionales independientes que gestionan sus propios pacientes, horarios, prestaciones y turnos."],
  ["¿Puedo administrar horarios y disponibilidad?", "Sí. Podés definir tus días de atención, franjas horarias, excepciones y vacaciones para ordenar tu agenda."],
  ["¿Puedo gestionar pacientes y turnos?", "Sí. Podés buscar pacientes, consultar sus fichas, crear turnos y organizar los próximos turnos desde la agenda."],
  ["¿Puedo registrar la evolución de mis pacientes?", "Sí. Turnelia permite registrar evoluciones y consultar posteriormente el seguimiento de la atención."],
  ["¿Puedo reprogramar turnos?", "Sí. La agenda permite organizar y actualizar los turnos según la disponibilidad configurada."],
  ["¿Necesito instalar un programa?", "No. Turnelia funciona desde el navegador, sin instalar un programa."],
  ["¿Puedo usar Turnelia desde el celular?", "Sí. Podés acceder desde computadora, tablet o celular con conexión a Internet."],
  ["¿Turnelia envía recordatorios de turnos?", "Sí. Turnelia envía recordatorios automáticos por email antes de los turnos."],
] as const;

function SoftwareHeader() {
  const [abierto, setAbierto] = useState(false);
  return <header className="landing-header seo-landing-header"><div className="landing-container landing-header__inner">
    <a className="landing-logo" href="/" aria-label="Turnelia, inicio"><img src="/brand/mediturnos-logo-horizontal.svg" alt="Turnelia" /></a>
    <button className="menu-button" type="button" aria-expanded={abierto} aria-controls="seo-navigation" onClick={() => setAbierto(!abierto)}><span /><span /><span /><span className="sr-only">Abrir menú</span></button>
    <nav id="seo-navigation" className={abierto ? "landing-nav is-open" : "landing-nav"} aria-label="Navegación principal" onClick={() => setAbierto(false)}><a href="#funciones">Funciones</a><a href="#como-empezar">Cómo empezar</a><a href="/sistema-de-turnos">Sistema de turnos</a><a href="/ayuda">Centro de Ayuda</a><a className="nav-login" href="/login">Ingresar</a><a className="button button--small" href="/registro">Probar Turnelia</a></nav>
  </div></header>;
}

function Faq() {
  const [abierta, setAbierta] = useState<number | null>(null);
  return <section id="preguntas-frecuentes" className="landing-section seo-faq"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Preguntas frecuentes</p><h2>Todo más claro antes de empezar</h2></div><div className="faq__list">{preguntas.map(([pregunta, respuesta], index) => { const activa = index === abierta; const id = `seo-faq-${index}`; return <div className={`faq__item${activa ? " is-open" : ""}`} key={pregunta}><h3><button type="button" aria-expanded={activa} aria-controls={id} onClick={() => setAbierta(activa ? null : index)}><span>{pregunta}</span><span className="faq__indicator" aria-hidden="true">{activa ? "−" : "+"}</span></button></h3><div id={id} className="faq__answer" hidden={!activa}><p>{respuesta}</p></div></div>; })}</div></div></section>;
}

function StructuredData() {
  useEffect(() => { const data = { "@context": "https://schema.org", "@graph": [
    { "@type": "WebPage", "@id": "https://turnelia.com.ar/software-para-consultorios", "url": "https://turnelia.com.ar/software-para-consultorios", "name": "Software para consultorios | Turnelia", "description": "Gestioná turnos, pacientes, historia clínica, horarios y prestaciones desde una sola plataforma. Turnelia simplifica la gestión diaria de tu consultorio." },
    { "@type": "SoftwareApplication", "name": "Turnelia", "applicationCategory": "BusinessApplication", "operatingSystem": "Web" },
    { "@type": "BreadcrumbList", "itemListElement": [{ "@type": "ListItem", "position": 1, "name": "Inicio", "item": "https://turnelia.com.ar/" }, { "@type": "ListItem", "position": 2, "name": "Software para consultorios", "item": "https://turnelia.com.ar/software-para-consultorios" }] },
    { "@type": "FAQPage", "mainEntity": preguntas.map(([name, text]) => ({ "@type": "Question", name, acceptedAnswer: { "@type": "Answer", text } })) },
  ] }; const script = document.createElement("script"); script.type = "application/ld+json"; script.textContent = JSON.stringify(data); document.head.append(script); return () => script.remove(); }, []);
  return null;
}

export default function SoftwareConsultoriosPage() {
  function medirRegistro(evento: React.MouseEvent<HTMLDivElement>) { if ((evento.target as Element).closest('a[href="/registro"]')) trackEvent("sign_up_click", { source: "software_consultorios" }); }
  return <div className="landing-page seo-landing" onClick={medirRegistro}><StructuredData /><SoftwareHeader /><main>
    <section className="seo-hero"><div className="landing-container seo-hero__grid"><div><p className="eyebrow">Gestión profesional</p><h1>Software para consultorios simple y completo</h1><p className="seo-hero__lead">Organizá turnos, pacientes, horarios, prestaciones y seguimiento de la atención desde un solo lugar. Turnelia te ayuda a simplificar la gestión diaria de tu consultorio sin planillas ni herramientas separadas.</p><div className="button-row"><a className="button" href="/registro">Probar Turnelia</a><a className="button button--outline" href="#funciones">Ver cómo funciona</a></div></div><figure className="seo-hero__image"><img src={LANDING_ASSETS.dashboard} alt="Agenda y gestión de Turnelia en una pantalla" loading="eager" fetchPriority="high" decoding="async" /></figure></div></section>
    <section className="seo-problems"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Menos tareas dispersas</p><h2>Una forma más ordenada de gestionar tu consultorio</h2><p>Centralizá lo que necesitás para trabajar con más claridad durante el día.</p></div><div className="seo-problems__grid">{["Turnos dispersos en distintos canales", "Agenda difícil de organizar y reprogramar", "Pacientes repartidos en múltiples planillas", "Horarios y disponibilidad difíciles de mantener", "Seguimiento de la atención separado"].map(item => <article key={item}><span aria-hidden="true">✓</span><h3>{item}</h3></article>)}</div></div></section>
    <section id="funciones" className="landing-section seo-functions"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Funciones principales</p><h2>Todo lo necesario para la gestión de consultorios</h2></div><div className="features__grid">{funciones.map(([title, text]) => <article key={title}><h3>{title}</h3><p>{text}</p></article>)}</div></div></section>
    <section className="landing-section seo-showcase"><div className="landing-container seo-showcase__grid"><div><p className="eyebrow">Agenda y turnos</p><h2>Organizá tu día con una agenda clara</h2><p>Consultá próximos turnos, estados y disponibilidad; creá o reprogramá cada atención desde la vista de agenda.</p><ul><li>Vista de agenda y próximos turnos</li><li>Estados de cada atención</li><li>Disponibilidad para ordenar la jornada</li></ul></div><img src={LANDING_ASSETS.dashboard} alt="Vista demo de agenda profesional de Turnelia" loading="lazy" /></div></section>
    <section className="landing-section seo-showcase seo-showcase--reverse"><div className="landing-container seo-showcase__grid"><div><p className="eyebrow">Gestión de pacientes</p><h2>La información de tus pacientes, organizada</h2><p>Buscá por nombre, DNI o teléfono, consultá la ficha y accedé al seguimiento de la atención desde un mismo lugar.</p></div><img src={LANDING_ASSETS.pacientes} alt="Ficha demo de pacientes en Turnelia" loading="lazy" /></div></section>
    <section className="landing-section seo-showcase"><div className="landing-container seo-showcase__grid"><div><p className="eyebrow">Horarios, disponibilidad y prestaciones</p><h2>Configurá Turnelia según tu forma de trabajar</h2><p>Definí días, franjas horarias, excepciones y vacaciones. Además, organizá tus prestaciones y sus duraciones para que la agenda refleje tu actividad.</p></div><img src={LANDING_ASSETS.disponibilidad} alt="Configuración demo de disponibilidad en Turnelia" loading="lazy" /></div></section>
    <section className="landing-section seo-audience"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Para quién sirve</p><h2>Para profesionales que gestionan pacientes y turnos</h2></div><div className="audience__list">{["Psicólogos", "Psicopedagogos", "Kinesiólogos", "Nutricionistas", "Médicos independientes", "Otros profesionales"].map(item => <span key={item}>{item}</span>)}</div></div></section>
    <section id="como-empezar" className="landing-section seo-steps"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Cómo empezar</p><h2>Empezá a organizar tu consultorio en pocos pasos</h2></div><ol>{["Crear tu cuenta", "Configurar tu perfil", "Cargar tus prestaciones", "Definir tu disponibilidad", "Empezar a gestionar pacientes y turnos"].map((item, index) => <li key={item}><span>{index + 1}</span><strong>{item}</strong></li>)}</ol></div></section>
    <Faq /><section className="dark-cta dark-cta--final"><div className="landing-container dark-cta__inner"><div><p className="eyebrow">Turnelia</p><h2>Organizá tu consultorio con Turnelia</h2><p>Probá una gestión más simple para tu actividad diaria.</p></div><a className="button button--light" href="/registro">Probar Turnelia</a></div></section>
  </main><footer className="landing-footer"><div className="landing-container seo-footer"><img src="/brand/mediturnos-logo-horizontal.svg" alt="Turnelia" /><div><a href="/">Inicio</a><a href="/sistema-de-turnos">Sistema de turnos</a><a href="/ayuda">Centro de Ayuda</a><a href="/registro">Probar Turnelia</a></div></div></footer></div>;
}
