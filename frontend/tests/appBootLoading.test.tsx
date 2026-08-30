import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";
import { iniciarSesion, obtenerUsuarioActual } from "../src/services/authService";
import { obtenerOnboarding } from "../src/services/onboardingService";
import { restaurarSesion } from "../src/utils/sesion";

vi.mock("../src/services/authService", () => ({
  iniciarSesion: vi.fn(),
  obtenerUsuarioActual: vi.fn(),
  solicitarRecuperacion: vi.fn(),
  restablecerPassword: vi.fn(),
}));
vi.mock("../src/services/onboardingService", () => ({ obtenerOnboarding: vi.fn() }));
vi.mock("../src/utils/sesion", () => ({ restaurarSesion: vi.fn() }));
vi.mock("../src/components/DashboardProfesional", () => ({ default: () => <div>Dashboard profesional listo</div> }));
vi.mock("../src/components/Dashboard", () => ({ default: () => <div>Dashboard listo</div> }));
vi.mock("../src/components/LandingPage", () => ({ default: () => <div>Landing</div> }));

const profesional = { nombre: "Sofía", rol: "profesional" } as const;
const onboardingCompleto = { onboarding_step: "completado" } as const;

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

async function flush() {
  await act(async () => { await Promise.resolve(); });
}

function renderLogin() {
  window.history.replaceState({}, "", "/login");
  render(<App />);
}

function submitLogin() {
  fireEvent.change(screen.getByLabelText("Correo electrónico"), { target: { value: "sofia@example.com" } });
  fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "password" } });
  fireEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));
}

describe("App boot loading", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    localStorage.clear();
    vi.mocked(restaurarSesion).mockResolvedValue(null);
    vi.mocked(obtenerOnboarding).mockResolvedValue(onboardingCompleto);
  });

  it("no muestra loader ni agrega espera en login rápido", async () => {
    vi.mocked(iniciarSesion).mockResolvedValue({ access_token: "token" });
    vi.mocked(obtenerUsuarioActual).mockResolvedValue(profesional);
    renderLogin();
    await flush();
    submitLogin();
    await flush();
    expect(screen.queryByLabelText("Preparando tu espacio")).not.toBeInTheDocument();
    expect(screen.getByText("Dashboard profesional listo")).toBeInTheDocument();
    expect(obtenerOnboarding).toHaveBeenCalledTimes(1);
  });

  it("muestra sólo las etapas reales después de 600 ms y navega al resolver", async () => {
    const auth = deferred<{ access_token: string }>();
    const me = deferred<typeof profesional>();
    const onboarding = deferred<typeof onboardingCompleto>();
    vi.mocked(iniciarSesion).mockReturnValue(auth.promise);
    vi.mocked(obtenerUsuarioActual).mockReturnValue(me.promise);
    vi.mocked(obtenerOnboarding).mockReturnValue(onboarding.promise);
    renderLogin();
    await flush();
    submitLogin();
    await act(async () => { auth.resolve({ access_token: "token" }); await Promise.resolve(); });
    expect(screen.queryByLabelText("Preparando tu espacio")).not.toBeInTheDocument();
    await act(async () => { vi.advanceTimersByTime(600); });
    expect(screen.getByLabelText("Preparando tu espacio")).toBeInTheDocument();
    expect(screen.getByText("Validando tu cuenta").previousElementSibling).not.toHaveTextContent("✓");
    me.resolve(profesional);
    await flush();
    expect(screen.getByText("Validando tu cuenta").previousElementSibling).toHaveTextContent("✓");
    expect(screen.getByText("Preparando tu espacio").previousElementSibling).not.toHaveTextContent("✓");
    onboarding.resolve(onboardingCompleto);
    await flush();
    expect(screen.getByText("Dashboard profesional listo")).toBeInTheDocument();
    expect(screen.queryByLabelText("Preparando tu espacio")).not.toBeInTheDocument();
    expect(vi.getTimerCount()).toBe(0);
  });

  it("sale inmediatamente a los 2000 ms y no espera el mensaje de 7 segundos", async () => {
    const onboarding = deferred<typeof onboardingCompleto>();
    vi.mocked(iniciarSesion).mockResolvedValue({ access_token: "token" });
    vi.mocked(obtenerUsuarioActual).mockResolvedValue(profesional);
    vi.mocked(obtenerOnboarding).mockReturnValue(onboarding.promise);
    renderLogin();
    await flush();
    submitLogin();
    await flush();
    await act(async () => { vi.advanceTimersByTime(600); });
    expect(screen.getByLabelText("Preparando tu espacio")).toBeInTheDocument();
    await act(async () => { vi.advanceTimersByTime(1400); });
    onboarding.resolve(onboardingCompleto);
    await flush();
    expect(screen.getByText("Dashboard profesional listo")).toBeInTheDocument();
    expect(screen.queryByText(/Estamos tardando/)).not.toBeInTheDocument();
  });

  it("cambia sólo el mensaje después de 7 segundos y no dispara requests", async () => {
    const onboarding = deferred<typeof onboardingCompleto>();
    vi.mocked(iniciarSesion).mockResolvedValue({ access_token: "token" });
    vi.mocked(obtenerUsuarioActual).mockResolvedValue(profesional);
    vi.mocked(obtenerOnboarding).mockReturnValue(onboarding.promise);
    renderLogin();
    await flush();
    submitLogin();
    await flush();
    await act(async () => { vi.advanceTimersByTime(7000); });
    expect(screen.getByText(/Estamos tardando un poco más/)).toBeInTheDocument();
    expect(iniciarSesion).toHaveBeenCalledTimes(1);
    expect(obtenerUsuarioActual).toHaveBeenCalledTimes(1);
    expect(obtenerOnboarding).toHaveBeenCalledTimes(1);
    onboarding.resolve(onboardingCompleto);
    await flush();
    expect(screen.getByText("Dashboard profesional listo")).toBeInTheDocument();
  });

  it("restaura sesión sin inventar login y sin hacer POST", async () => {
    localStorage.setItem("access_token", "token");
    vi.mocked(restaurarSesion).mockResolvedValue(profesional);
    renderLogin();
    await flush();
    expect(screen.getByText("Dashboard profesional listo")).toBeInTheDocument();
    expect(iniciarSesion).not.toHaveBeenCalled();
    expect(screen.queryByText("Iniciando sesión")).not.toBeInTheDocument();
  });

  it("permite reintentar tras un error sin ejecutar secuencias concurrentes", async () => {
    vi.mocked(iniciarSesion).mockRejectedValueOnce(new Error("network"));
    renderLogin();
    await flush();
    submitLogin();
    await flush();
    expect(screen.getByText("Ocurrió un error inesperado.")).toBeInTheDocument();
    vi.mocked(iniciarSesion).mockResolvedValueOnce({ access_token: "token" });
    vi.mocked(obtenerUsuarioActual).mockResolvedValueOnce(profesional);
    submitLogin();
    await flush();
    expect(screen.getByText("Dashboard profesional listo")).toBeInTheDocument();
    expect(iniciarSesion).toHaveBeenCalledTimes(2);
  });
});
