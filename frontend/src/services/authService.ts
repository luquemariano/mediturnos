import api from "../api/api";

import type {
  LoginRequest,
  LoginResponse,
  UsuarioActual,
} from "../types/auth";


export async function iniciarSesion(
  datos: LoginRequest,
): Promise<LoginResponse> {
  const respuesta = await api.post<LoginResponse>(
    "/auth/login",
    datos,
  );

  return respuesta.data;
}


export async function obtenerUsuarioActual():
Promise<UsuarioActual> {
  const respuesta = await api.get<UsuarioActual>(
    "/auth/me",
  );

  return respuesta.data;
}