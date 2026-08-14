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

export interface MensajeResponse { mensaje: string; }
export interface ForgotPasswordRequest { email: string; }
export interface ResetPasswordRequest { token: string; new_password: string; }
export interface ChangePasswordRequest { current_password: string; new_password: string; }
