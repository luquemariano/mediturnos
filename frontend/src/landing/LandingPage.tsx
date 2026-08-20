import { useState } from "react";
import { LANDING_ASSETS, PLANES, WHATSAPP_URL } from "./landingConfig";
import "./LandingPage.css";

const funciones = [
  ["Agenda profesional", "Visualizá tus turnos del día y gestioná cada atención."],
  ["Pacientes", "Creá pacientes y encontralos rápidamente por nombre, DNI o teléfono."],
  ["Disponibilidad", "Definí días, horarios de atención, excepciones y vacaciones."],
  ["Prestaciones", "Configurá los servicios que ofrecés y organizá tu actividad profesional."],
  ["Recordatorios automáticos", "Recordá cada turno por email y permití que tus pacientes confirmen o cancelen con un clic."],
  ["Multidispositivo", "Usá Turnelia desde computadora, tablet o celular."],
];

const iconos = ["calendar", "users", "clock", "briefcase", "bell", "devices"];

function LineIcon({ name }: { name: string }) {
  const paths: Record<string, React.ReactNode> = {
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4m8-4v4M3 10h18"/></>,
    users: <><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0m2-13a3 3 0 0 1 0 6m1 3a5 5 0 0 1 3 4"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    briefcase: <><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V4h8v3m-13 5h18"/></>,
    account: <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
    devices: <><rect x="2" y="4" width="14" height="11" rx="1"/><path d="M7 19h4m-2-4v4"/><rect x="18" y="8" width="4" height="10" rx="1"/></>,
    shield: <><path d="M12 3 4 6v5c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6l-8-3Z"/><path d="m9 12 2 2 4-4"/></>,
    bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></>,
  };
  return <svg className="landing-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">{paths[name]}</svg>;
}

function ReminderEmailVisual() {
  return <div className="reminder-email" aria-label="Vista ilustrativa de un email de recordatorio de turno">
    <div className="reminder-email__top"><span className="reminder-email__dot" aria-hidden="true" /><strong>Turnelia</strong><span>•••</span></div>
    <div className="reminder-email__body"><p className="eyebrow">Recordatorio de turno</p><h3>Tu próximo turno</h3><p className="reminder-email__date">19/08/2026 · 20:50</p><div className="reminder-email__details"><span>Profesional</span><strong>Dra. Sofía Ramírez</strong><span>Especialidad</span><strong>Consulta demo</strong></div><p>¿Vas a asistir? Confirmá o cancelá tu turno desde este email.</p><div className="reminder-email__actions"><button className="button" type="button" aria-label="Botón ilustrativo confirmar turno">Confirmar turno</button><button className="button button--outline" type="button" aria-label="Botón ilustrativo cancelar turno">Cancelar turno</button></div></div>
  </div>;
}

function ProductImage({ asset, label, variant }: { asset: string; label: string; variant?: "prestaciones" | "security" }) {
  const [disponible, setDisponible] = useState(true);

  if (!disponible) {
    return (
      <div className="product-placeholder" role="img" aria-label={`${label}. Captura no disponible.`}>
        <span>Vista del producto</span>
        <strong>{label}</strong>
      </div>
    );
  }

  return (
    <figure className={`product-image${variant ? ` product-image--${variant}` : ""}`}>
      <img src={asset} alt={label} loading="lazy" onError={() => setDisponible(false)} />
    </figure>
  );
}

function HeroDevice({ tipo, asset, label }: { tipo: "notebook" | "tablet" | "phone"; asset: string; label: string }) {
  return (
    <figure className={`hero-device hero-device--${tipo}`}>
      <div className="hero-device__screen">
        <img src={asset} alt={label} />
      </div>
      {tipo === "notebook" && <span className="hero-device__base" aria-hidden="true" />}
      {tipo === "phone" && <span className="hero-device__speaker" aria-hidden="true" />}
    </figure>
  );
}

function LandingHeader() {
  const [abierto, setAbierto] = useState(false);
  return <header className="landing-header">
    <div className="landing-container landing-header__inner">
      <a className="landing-logo" href="#inicio" aria-label="Turnelia, inicio"><img src="/brand/mediturnos-logo-horizontal.svg" alt="Turnelia" /></a>
      <button className="menu-button" type="button" aria-expanded={abierto} aria-controls="landing-navigation" onClick={() => setAbierto(!abierto)}><span></span><span></span><span></span><span className="sr-only">Abrir menú</span></button>
      <nav id="landing-navigation" className={abierto ? "landing-nav is-open" : "landing-nav"} aria-label="Navegación principal" onClick={() => setAbierto(false)}>
        <a href="#funciones">Funciones</a><a href="#profesionales">Para profesionales</a><a href="#precios">Precios</a><a href="#demo">Demo</a><a href="#contacto">Contacto</a>
        <a className="nav-login" href="/login">Ingresar</a><a className="button button--small" href="/registro">Probar Turnelia</a>
      </nav>
    </div>
  </header>;
}

function Showcase({ id, eyebrow, title, text, bullets, asset, reverse = false, imageVariant }: { id?: string; eyebrow: string; title: string; text: string; bullets: string[]; asset: string; reverse?: boolean; imageVariant?: "prestaciones" }) {
  return <section id={id} className={`landing-section showcase ${reverse ? "showcase--reverse" : ""}`}>
    <div className="landing-container showcase__grid">
      <div className="showcase__copy"><p className="eyebrow">{eyebrow}</p><h2>{title}</h2><p>{text}</p><ul>{bullets.map(item => <li key={item}>{item}</li>)}</ul></div>
      <ProductImage asset={asset} label={`Pantalla real de ${eyebrow.toLowerCase()} en Turnelia`} variant={imageVariant} />
    </div>
  </section>;
}

export default function LandingPage() {
  return <div className="landing-page">
    <LandingHeader />
    <main>
      <section id="inicio" className="hero"><div className="landing-container hero__grid">
        <div className="hero__copy"><p className="eyebrow">Agenda y gestión profesional</p><h1>La agenda profesional que ordena tu consulta</h1><p className="hero__lead">Turnelia reúne tu agenda, pacientes, disponibilidad, prestaciones y recordatorios automáticos en un solo lugar. Organizá tu trabajo diario desde cualquier dispositivo, sin instalaciones ni complicaciones.</p><div className="button-row"><a className="button" href="/registro">Probar Turnelia</a><a className="button button--outline" href="#funciones">Ver cómo funciona</a></div></div>
        <div className="hero-devices" aria-label="Turnelia en notebook, tablet y teléfono">
          <HeroDevice tipo="notebook" asset={LANDING_ASSETS.dashboard} label="Dashboard profesional real de Turnelia en notebook" />
          <HeroDevice tipo="tablet" asset={LANDING_ASSETS.pacientes} label="Módulo real de pacientes de Turnelia en tablet" />
          <HeroDevice tipo="phone" asset={LANDING_ASSETS.dashboardMobile} label="Dashboard móvil real de Turnelia" />
        </div>
      </div></section>
      <section className="benefits" aria-label="Ventajas de Turnelia"><div className="landing-container benefits__grid">{[["En la nube", "Accedé desde cualquier lugar."], ["En cualquier dispositivo", "Computadora, tablet o celular."], ["Acceso protegido", "Cada profesional trabaja con su propia cuenta."]].map(([title, text], index) => <article key={title}><LineIcon name={index === 1 ? "devices" : index === 2 ? "shield" : "clock"}/><div><h2>{title}</h2><p>{text}</p></div></article>)}</div></section>
      <section id="funciones" className="landing-section features"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Funciones</p><h2>Todo lo que necesitás para organizar tu consulta</h2></div><div className="features__grid">{funciones.map(([title, text], index) => <article key={title}><LineIcon name={iconos[index]}/><h3>{title}</h3><p>{text}</p></article>)}</div></div></section>
      <Showcase eyebrow="Agenda" title="Tu día, claro desde el primer vistazo" text="Al ingresar a Turnelia sabés qué pacientes tenés, a qué hora llegan y cómo está organizada tu jornada." bullets={["Próximos turnos", "Estado de cada atención", "Acceso rápido a la agenda", "Disponibilidad del día"]} asset={LANDING_ASSETS.dashboard}/>
      <section id="recordatorios" className="landing-section reminder-showcase"><div className="landing-container reminder-showcase__grid"><div className="showcase__copy"><p className="eyebrow">Recordatorios automáticos</p><h2>Menos ausencias. Más control sobre tu agenda.</h2><p>Turnelia recuerda automáticamente los próximos turnos y permite que cada paciente confirme o cancele su asistencia desde el mismo email.</p><ul><li>Recordatorios automáticos antes del turno</li><li>Confirmación directa desde el email</li><li>Cancelación sin llamadas ni mensajes</li><li>El estado se actualiza automáticamente en tu agenda</li></ul><p className="reminder-showcase__microcopy">El paciente responde en segundos y la agenda se actualiza automáticamente.</p></div><ReminderEmailVisual /></div></section>
      <Showcase eyebrow="Pacientes" title="Tus pacientes, siempre a mano" text="Buscá rápidamente a cada paciente y accedé a la información necesaria para gestionar su atención." bullets={["Búsqueda por nombre, DNI o teléfono", "Información accesible para gestionar la atención", "Historia clínica y evoluciones"]} asset={LANDING_ASSETS.pacientes} reverse/>
      <Showcase eyebrow="Disponibilidad" title="Tus horarios se adaptan a tu forma de trabajar" text="Definí cuándo atendés y Turnelia organiza la disponibilidad alrededor de tu práctica profesional." bullets={["Días de atención", "Franjas horarias", "Excepciones", "Vacaciones y días no laborables"]} asset={LANDING_ASSETS.disponibilidad}/>
      <Showcase eyebrow="Prestaciones" title="Organizá los servicios que ofrecés" text="Configurá las prestaciones de tu consulta para que la agenda represente realmente la manera en que trabajás." bullets={["Servicios de tu consulta", "Actividad profesional organizada"]} asset={LANDING_ASSETS.prestaciones} reverse imageVariant="prestaciones"/>
      <section className="landing-section future"><div className="landing-container future__inner"><p className="eyebrow">En desarrollo</p><h2>Más herramientas para acompañar tu práctica</h2><p>Seguimos incorporando mejoras para que Turnelia acompañe la evolución de cada consulta.</p></div></section>
      <section className="landing-section security"><div className="landing-container showcase__grid"><div className="showcase__copy"><p className="eyebrow">Seguridad</p><h2>Tu información profesional, protegida</h2><div className="security__list">{["Cuenta personal", "Autenticación protegida", "Permisos según usuario", "Recuperación de acceso", "Conexión HTTPS", "Infraestructura cloud"].map(item => <span key={item}><LineIcon name="shield"/>{item}</span>)}</div></div><ProductImage asset={LANDING_ASSETS.loginSecurity} label="Pantalla real de acceso a Turnelia" variant="security" /></div></section>
      <section id="precios" className="landing-section pricing"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Precios</p><h2>Planes simples para crecer con Turnelia</h2><p>Elegí la opción que mejor se adapte a tu forma de trabajar.</p></div><div className="pricing__grid">{PLANES.map(plan => <article className={plan.destacado ? "plan plan--featured" : "plan"} key={plan.nombre}><span className="plan__status">{plan.estado}</span><h3>{plan.nombre}</h3><p>{plan.descripcion}</p><p className="plan__price">{plan.precio}</p><ul>{plan.incluye.map(item => <li key={item}>{item}</li>)}</ul><a className="button button--outline" href={plan.href}>{plan.accion}</a></article>)}</div><div className="pricing__payment"><img src="/brand/mercadopago.svg" alt="Mercado Pago" /><span>Pagos seguros con Mercado Pago</span></div><p className="pricing__note">*Sujeto a política de uso razonable.</p></div></section>
      <section id="demo" className="dark-cta"><div className="landing-container dark-cta__inner"><div><p className="eyebrow">Demo</p><h2>Conocé Turnelia funcionando</h2><p>Creá tu cuenta y probá Turnelia con 14 días de acceso gratuito.</p></div><a className="button button--light" href="/registro">Probar Turnelia</a></div></section>
      <section id="profesionales" className="landing-section audience"><div className="landing-container"><div className="section-heading"><p className="eyebrow">Para quién es</p><h2>Pensado para profesionales que gestionan su propia consulta</h2></div><div className="audience__list">{["Médicos", "Psicólogos", "Psiquiatras", "Psicopedagogos", "Nutricionistas", "Kinesiólogos", "Otros profesionales independientes"].map(item => <span key={item}>{item}</span>)}</div></div></section>
      <section id="contacto" className="dark-cta dark-cta--final"><div className="landing-container dark-cta__inner"><div><h2>Menos tiempo organizando. Más tiempo para tus pacientes.</h2><p>Empezá a ordenar tu consulta con Turnelia.</p><div className="landing-contacto"><a href="mailto:marianoluque@live.com">marianoluque@live.com</a><a href={WHATSAPP_URL}>+54 9 351 227 7416</a></div></div><div className="button-row"><a className="button button--light" href="/registro">Probar Turnelia</a>{WHATSAPP_URL ? <a className="button button--dark-outline" href={WHATSAPP_URL} target="_blank" rel="noreferrer">Hablar por WhatsApp</a> : <button className="button button--dark-outline" disabled title="Canal de WhatsApp pendiente de configurar">Hablar por WhatsApp</button>}</div></div></section>
    </main>
    <footer className="landing-footer"><div className="landing-container landing-footer__grid"><div><img src="/brand/mediturnos-logo-horizontal.svg" alt="Turnelia"/><p>Agenda y gestión profesional.</p></div><div><h2>Producto</h2><a href="#funciones">Funciones</a><a href="#precios">Precios</a><a href="#demo">Demo</a></div><div><h2>Turnelia</h2><a href="#contacto">Contacto</a><span>Privacidad</span><span>Términos</span></div><div><h2>Acceso</h2><a href="/login">Ingresar</a></div></div><div className="landing-container landing-footer__bottom">© 2026 Turnelia. Todos los derechos reservados.</div></footer>
  </div>;
}
