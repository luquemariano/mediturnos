import api from "../api/api";
import type {
  EstadoTurno,
  Turno,
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