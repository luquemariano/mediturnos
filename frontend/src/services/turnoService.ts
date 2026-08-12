import api from "../api/api";
import type {
  EstadoTurno,
  HorarioLibre,
  Turno,
  TurnoCrear,
} from "../types/turno";


export async function obtenerTurnos():
Promise<Turno[]> {
  const respuesta = await api.get<Turno[]>(
    "/turnos/",
  );

  return respuesta.data;
}


export async function cambiarEstadoTurno(
  turnoId: number,
  estado: EstadoTurno,
): Promise<Turno> {
  const respuesta = await api.patch<Turno>(
    `/turnos/${turnoId}/estado`,
    {
      estado,
    },
  );

  return respuesta.data;
}

export async function crearTurno(
  datos: TurnoCrear,
): Promise<Turno> {
  const respuesta = await api.post<Turno>(
    "/turnos/",
    datos,
  );

  return respuesta.data;
}

export async function obtenerHorariosLibres(
  prestacionId: number,
  fecha: string,
  turnoIdExcluido?: number,
): Promise<HorarioLibre[]> {
  const respuesta = await api.get<HorarioLibre[]>(
    "/disponibilidades/horarios-libres/",
    {
      params: {
        prestacion_id: prestacionId,
        fecha,
        turno_id_excluido: turnoIdExcluido,
      },
    },
  );

  return respuesta.data;
}

export async function reprogramarTurno(
  turnoId: number,
  fechaHora: string,
): Promise<Turno> {
  const respuesta = await api.patch<Turno>(
    `/turnos/${turnoId}/reprogramar`,
    {
      fecha_hora: fechaHora,
    },
  );

  return respuesta.data;
}
