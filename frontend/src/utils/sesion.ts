import axios from "axios";

import type { UsuarioActual } from "../types/auth";


type ObtenerUsuario = () => Promise<UsuarioActual>;


export async function restaurarSesion(
  obtenerUsuario: ObtenerUsuario,
  almacenamiento: Pick<Storage, "getItem" | "removeItem"> =
    localStorage,
): Promise<UsuarioActual | null> {
  const token = almacenamiento.getItem("access_token");

  if (!token) {
    return null;
  }

  try {
    return await obtenerUsuario();
  } catch (error) {
    if (
      axios.isAxiosError(error)
      && error.response?.status === 401
    ) {
      almacenamiento.removeItem("access_token");
    }

    return null;
  }
}
