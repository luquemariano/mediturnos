type DashboardProps = {
  nombre: string;
  rol: string;
  onAbrirPacientes: () => void;
  onAbrirProfesionales: () => void;
  onAbrirEspecialidades: () => void;
  onAbrirPrestaciones: () => void;
  onAbrirTurnos: () => void;
  onAbrirDisponibilidades: () => void;
  onAbrirPerfil: () => void;
  onAbrirCuentas: () => void;
  onCerrarSesion: () => void;
};

type Modulo = { titulo: string; descripcion: string; icono: string; accion?: () => void };

function Dashboard(props: DashboardProps) {
  const esAdministrador = props.rol === "administrador";
  const operativos: Modulo[] = [
    { titulo: "Pacientes", descripcion: "Consultar y administrar pacientes.", icono: "👥", accion: props.onAbrirPacientes },
    { titulo: "Profesionales", descripcion: "Consultar profesionales.", icono: "🩺", accion: props.onAbrirProfesionales },
    { titulo: "Prestaciones", descripcion: "Gestionar servicios.", icono: "✚", accion: props.onAbrirPrestaciones },
    { titulo: "Turnos", descripcion: "Consultar y gestionar la agenda.", icono: "📅", accion: props.onAbrirTurnos },
    { titulo: "Disponibilidades", descripcion: "Configurar horarios profesionales.", icono: "◷", accion: props.onAbrirDisponibilidades },
  ];
  const modulosPorRol: Record<string, Modulo[]> = {
    administrador: [
      { titulo: "Cuentas", descripcion: "Gestionar cuentas, planes y suscripciones.", icono: "▦", accion: props.onAbrirCuentas },
      { titulo: "Profesionales", descripcion: "Consultar profesionales registrados.", icono: "🩺", accion: props.onAbrirProfesionales },
      { titulo: "Especialidades", descripcion: "Administrar el catálogo global.", icono: "✦", accion: props.onAbrirEspecialidades },
    ],
    recepcionista: operativos,
    profesional: [
      { titulo: "Mi agenda", descripcion: "Consultar y gestionar tus turnos.", icono: "📅", accion: props.onAbrirTurnos },
      { titulo: "Mi disponibilidad", descripcion: "Configurar tus horarios de atención.", icono: "◷", accion: props.onAbrirDisponibilidades },
      { titulo: "Mi perfil", descripcion: "Consultar tus datos profesionales.", icono: "👤", accion: props.onAbrirPerfil },
    ],
    paciente: [
      { titulo: "Mis turnos", descripcion: "Consultar y cancelar tus turnos.", icono: "📅", accion: props.onAbrirTurnos },
      { titulo: "Mi perfil", descripcion: "Consultar tus datos personales.", icono: "👤", accion: props.onAbrirPerfil },
    ],
  };
  const modulos = modulosPorRol[props.rol] ?? [];

  return <main className="pagina-dashboard"><section className="dashboard">
    <header className="dashboard-encabezado"><div className="marca dashboard-marca"><img className="marca-icono" src="/brand/mediturnos-symbol.svg" alt="" aria-hidden="true" /><div><h1>Turnelia</h1><p>Gestión médica simple y segura</p></div></div><div className="usuario-resumen"><div className="usuario-avatar">{props.nombre.charAt(0).toUpperCase()}</div><div><strong>{props.nombre}</strong><span>{props.rol}</span></div></div></header>
    <section className={`dashboard-bienvenida${esAdministrador ? " dashboard-bienvenida-admin" : ""}`}><div><p className="dashboard-etiqueta">{esAdministrador ? "Administración global" : "Panel principal"}</p><h2>{esAdministrador ? "Panel administrativo" : `Bienvenido, ${props.nombre}`}</h2><p>{esAdministrador ? "Gestioná cuentas, profesionales y el catálogo global de Turnelia." : "Accedé a los módulos disponibles para tu rol."}</p></div><span className="rol-badge">{props.rol}</span></section>
    <section className="dashboard-modulos">{modulos.map((modulo) => <button key={modulo.titulo} type="button" className="modulo-tarjeta" onClick={modulo.accion} disabled={!modulo.accion}><span className="modulo-icono">{modulo.icono}</span><span className="modulo-contenido"><strong>{modulo.titulo}</strong><small>{modulo.descripcion}</small></span><span className="modulo-flecha">{modulo.accion ? "→" : "Próximamente"}</span></button>)}</section>
    <footer className="dashboard-pie"><p>Sesión iniciada como <strong>{props.nombre}</strong></p><button type="button" className="boton-cerrar-sesion" onClick={props.onCerrarSesion}>Cerrar sesión</button></footer>
  </section></main>;
}

export default Dashboard;
