import api from "../api/api";
import type { PlanCode } from "../types/cuenta";
import type {
  EstadoSuscripcionSaas,
  InicioSuscripcionRespuesta,
} from "../types/suscripcion";

export async function obtenerSuscripcion(
  cuentaId: number,
): Promise<EstadoSuscripcionSaas> {
  return (await api.get<EstadoSuscripcionSaas>(
    `/cuentas/${cuentaId}/suscripcion`,
  )).data;
}

export async function iniciarSuscripcion(
  cuentaId: number,
  plan: PlanCode,
  cardTokenId: string,
): Promise<InicioSuscripcionRespuesta> {
  return (await api.post<InicioSuscripcionRespuesta>(
    `/cuentas/${cuentaId}/suscripcion/mercadopago/iniciar`,
    { plan, card_token_id: cardTokenId },
  )).data;
}

export async function sincronizarSuscripcion(
  cuentaId: number,
): Promise<{ procesado: boolean; suscripcion: EstadoSuscripcionSaas }> {
  return (await api.post<{ procesado: boolean; suscripcion: EstadoSuscripcionSaas }>(
    `/cuentas/${cuentaId}/suscripcion/mercadopago/sincronizar`,
  )).data;
}
