import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "../src/App";
import * as authService from "../src/services/authService";

vi.mock("../src/services/authService", () => ({
  iniciarSesion: vi.fn(), obtenerUsuarioActual: vi.fn(),
  solicitarRecuperacion: vi.fn(), restablecerPassword: vi.fn(),
}));
vi.mock("../src/utils/sesion", () => ({ restaurarSesion: vi.fn().mockResolvedValue(null) }));

beforeEach(() => {
  vi.clearAllMocks();
  window.history.replaceState({}, "", "/");
});

describe("recuperación de contraseña", () => {
  it("abre forgot, envía email y muestra respuesta genérica", async () => {
    vi.mocked(authService.solicitarRecuperacion).mockResolvedValue({
      mensaje: "Si existe una cuenta asociada a ese correo, recibirás instrucciones para restablecer tu contraseña.",
    });
    render(<App />);
    await screen.findByRole("button", { name: "¿Olvidaste tu contraseña?" });
    const simbolo = document.querySelector('.autenticacion-marca img[src="/brand/mediturnos-symbol.svg"]');
    expect(simbolo).toHaveAttribute("alt", "");
    expect(simbolo).toHaveAttribute("aria-hidden", "true");
    fireEvent.click(screen.getByRole("button", { name: "¿Olvidaste tu contraseña?" }));
    fireEvent.change(screen.getByLabelText("Correo electrónico"), { target: { value: "persona@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar instrucciones" }));
    expect(authService.solicitarRecuperacion).toHaveBeenCalledWith({ email: "persona@example.com" });
    expect(await screen.findByRole("status")).toHaveTextContent("Si existe una cuenta asociada");
  });

  it("muestra loading, bloquea submit y presenta error técnico", async () => {
    let rechazar!: (error: unknown) => void;
    vi.mocked(authService.solicitarRecuperacion).mockReturnValue(new Promise((_, reject) => { rechazar = reject; }));
    render(<App />);
    await screen.findByRole("button", { name: "¿Olvidaste tu contraseña?" });
    fireEvent.click(screen.getByRole("button", { name: "¿Olvidaste tu contraseña?" }));
    fireEvent.change(screen.getByLabelText("Correo electrónico"), { target: { value: "persona@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar instrucciones" }));
    expect(screen.getByRole("button", { name: "Enviando…" })).toBeDisabled();
    rechazar(new Error("red"));
    expect(await screen.findByRole("status")).toHaveTextContent("No pudimos enviar las instrucciones");
  });

  it("valida coincidencia y resetea usando el token de la URL", async () => {
    window.history.replaceState({}, "", "/reset-password?token=token-seguro");
    vi.mocked(authService.restablecerPassword).mockResolvedValue({ mensaje: "Tu contraseña fue actualizada." });
    render(<App />);
    await screen.findByRole("heading", { name: "Crear nueva contraseña" });
    fireEvent.change(screen.getByLabelText("Nueva contraseña"), { target: { value: "password-nueva" } });
    fireEvent.change(screen.getByLabelText("Repetir contraseña"), { target: { value: "distinta-password" } });
    fireEvent.click(screen.getByRole("button", { name: "Actualizar contraseña" }));
    expect(screen.getByRole("status")).toHaveTextContent("Las contraseñas no coinciden.");
    fireEvent.change(screen.getByLabelText("Repetir contraseña"), { target: { value: "password-nueva" } });
    fireEvent.click(screen.getByRole("button", { name: "Actualizar contraseña" }));
    expect(authService.restablecerPassword).toHaveBeenCalledWith({ token: "token-seguro", new_password: "password-nueva" });
    expect(await screen.findByRole("status")).toHaveTextContent("Tu contraseña fue actualizada.");
    fireEvent.click(screen.getByRole("button", { name: "Volver a iniciar sesión" }));
    expect(await screen.findByRole("button", { name: "Iniciar sesión" })).toBeInTheDocument();
  });

  it("muestra token inválido sin token y error del backend", async () => {
    window.history.replaceState({}, "", "/reset-password");
    render(<App />);
    await screen.findByRole("heading", { name: "Crear nueva contraseña" });
    fireEvent.change(screen.getByLabelText("Nueva contraseña"), { target: { value: "password-nueva" } });
    fireEvent.change(screen.getByLabelText("Repetir contraseña"), { target: { value: "password-nueva" } });
    fireEvent.click(screen.getByRole("button", { name: "Actualizar contraseña" }));
    expect(screen.getByRole("status")).toHaveTextContent("no es válido o venció");
  });
});
