export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UsuarioActual {
  id: number;
  nombre: string;
  email: string;
  rol: string;
  activo: boolean;
  creado_en: string;
}

export type OnboardingStep = "perfil" | "prestaciones" | "disponibilidad" | "listo" | "completado";
export interface RegistroProfesionalRequest { nombre: string; apellido: string; email: string; password: string; telefono?: string; matricula: string; especialidad_id: number; }
export interface RegistroProfesionalResponse extends LoginResponse { usuario_id: number; usuario: string; rol: string; profesional_id: number; onboarding_step: OnboardingStep; }

export interface MensajeResponse { mensaje: string; }
export interface ForgotPasswordRequest { email: string; }
export interface ResetPasswordRequest { token: string; new_password: string; }
export interface ChangePasswordRequest { current_password: string; new_password: string; }
