import axios from "axios";


export const EVENTO_SESION_NO_AUTORIZADA =
  "mediturnos:sesion-no-autorizada";

let tokenNotificado: string | null = null;


export function manejarErrorDeApi(
  error: unknown,
  almacenamiento: Pick<Storage, "getItem" | "removeItem"> =
    localStorage,
  notificar: () => void = () => {
    window.dispatchEvent(
      new Event(EVENTO_SESION_NO_AUTORIZADA),
    );
  },
) {
  if (
    !axios.isAxiosError(error)
    || error.response?.status !== 401
  ) {
    return Promise.reject(error);
  }

  const tokenActual = almacenamiento.getItem(
    "access_token",
  );

  almacenamiento.removeItem("access_token");

  if (tokenActual && tokenActual !== tokenNotificado) {
    tokenNotificado = tokenActual;
    notificar();
  }

  return Promise.reject(error);
}


export function habilitarNotificacionDeSesion() {
  tokenNotificado = null;
}
