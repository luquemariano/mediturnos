import api from "../api/api";

import type {
  LoginRequest,
  LoginResponse,
  UsuarioActual,
  ChangePasswordRequest,
  ForgotPasswordRequest,
  MensajeResponse,
  ResetPasswordRequest,
  RegistroProfesionalRequest,
  RegistroProfesionalResponse,
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

export async function registrarProfesional(datos: RegistroProfesionalRequest): Promise<RegistroProfesionalResponse> {
  return (await api.post<RegistroProfesionalResponse>("/auth/register/profesional", datos)).data;
}

export async function solicitarRecuperacion(
  datos: ForgotPasswordRequest,
): Promise<MensajeResponse> {
  return (await api.post<MensajeResponse>("/auth/forgot-password", datos)).data;
}

export async function restablecerPassword(
  datos: ResetPasswordRequest,
): Promise<MensajeResponse> {
  return (await api.post<MensajeResponse>("/auth/reset-password", datos)).data;
}

export async function cambiarPassword(
  datos: ChangePasswordRequest,
): Promise<MensajeResponse> {
  return (await api.post<MensajeResponse>("/auth/change-password", datos)).data;
}
