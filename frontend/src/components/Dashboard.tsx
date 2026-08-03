type DashboardProps = {
  nombre: string;
  rol: string;
  onAbrirPacientes: () => void;
  onAbrirTurnos: () => void;
  onCerrarSesion: () => void;
};


type Modulo = {
  titulo: string;
  descripcion: string;
  icono: string;
  accion?: () => void;
};


function formatearRol(
  rol: string,
): string {
  if (!rol) {
    return "Usuario";
  }

  return (
    rol.charAt(0).toUpperCase()
    + rol.slice(1)
  );
}


function Dashboard({
  nombre,
  rol,
  onAbrirPacientes,
  onAbrirTurnos,
  onCerrarSesion,
}: DashboardProps) {
  const modulos: Modulo[] = [
    {
      titulo: "Pacientes",
      descripcion:
        "Consultar y administrar la información de los pacientes.",
      icono: "👥",
      accion: onAbrirPacientes,
    },
    {
      titulo: "Profesionales",
      descripcion:
        "Gestionar profesionales, matrículas y especialidades.",
      icono: "🩺",
    },
    {
      titulo: "Turnos",
      descripcion:
        "Consultar reservas, estados y agenda médica.",
      icono: "📅",
      accion: onAbrirTurnos,
    },
    {
      titulo: "Pagos",
      descripcion:
        "Revisar pagos y operaciones vinculadas a los turnos.",
      icono: "💳",
    },
  ];


  return (
    <main className="pagina-dashboard">
      <section className="dashboard">
        <header className="dashboard-encabezado">
          <div className="marca dashboard-marca">
            <span className="marca-icono">
              +
            </span>

            <div>
              <h1>MediTurnos</h1>

              <p>
                Gestión médica simple y segura
              </p>
            </div>
          </div>

          <div className="usuario-resumen">
            <div className="usuario-avatar">
              {nombre
                .charAt(0)
                .toUpperCase()}
            </div>

            <div>
              <strong>{nombre}</strong>

              <span>
                {formatearRol(rol)}
              </span>
            </div>
          </div>
        </header>

        <section className="dashboard-bienvenida">
          <div>
            <p className="dashboard-etiqueta">
              Panel principal
            </p>

            <h2>
              Bienvenido, {nombre}
            </h2>

            <p>
              Desde este panel podés acceder
              a los principales módulos de
              MediTurnos.
            </p>
          </div>

          <span className="rol-badge">
            {formatearRol(rol)}
          </span>
        </section>

        <section className="dashboard-modulos">
          {modulos.map((modulo) => (
            <button
              key={modulo.titulo}
              type="button"
              className="modulo-tarjeta"
              onClick={modulo.accion}
              disabled={!modulo.accion}
            >
              <span className="modulo-icono">
                {modulo.icono}
              </span>

              <span className="modulo-contenido">
                <strong>
                  {modulo.titulo}
                </strong>

                <small>
                  {modulo.descripcion}
                </small>
              </span>

              <span className="modulo-flecha">
                {modulo.accion
                  ? "→"
                  : "Próximamente"}
              </span>
            </button>
          ))}
        </section>

        <footer className="dashboard-pie">
          <p>
            Sesión iniciada como{" "}
            <strong>{nombre}</strong>
          </p>

          <button
            type="button"
            className="boton-cerrar-sesion"
            onClick={onCerrarSesion}
          >
            Cerrar sesión
          </button>
        </footer>
      </section>
    </main>
  );
}

export default Dashboard;