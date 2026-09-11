import ProfesionalShell from "./ProfesionalShell";
import ReservaOnlinePanel from "./ReservaOnlinePanel";

type Props = { nombre: string; onVolver: () => void; onAbrirAgenda: () => void; onAbrirPacientes: () => void; onAbrirDisponibilidad: () => void; onAbrirPrestaciones: () => void; onAbrirPerfil: () => void; onCerrarSesion: () => void; };

export default function ReservaOnline(props: Props) {
  return <ProfesionalShell activo="reserva-online" nombre={props.nombre} tituloTopbar="Reserva online" onAbrirInicio={props.onVolver} onAbrirAgenda={props.onAbrirAgenda} onAbrirPacientes={props.onAbrirPacientes} onAbrirDisponibilidad={props.onAbrirDisponibilidad} onAbrirPrestaciones={props.onAbrirPrestaciones} onAbrirReservaOnline={() => undefined} onAbrirPerfil={props.onAbrirPerfil} onCerrarSesion={props.onCerrarSesion}>
    <div className="mis-prestaciones"><header><div><span>Reservas públicas</span><h1>Reserva online</h1><p>Compartí tu enlace para que tus pacientes puedan reservar horarios disponibles sin ingresar a Turnelia.</p></div></header><ReservaOnlinePanel /></div>
  </ProfesionalShell>;
}
