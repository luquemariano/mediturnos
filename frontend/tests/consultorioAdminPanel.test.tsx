import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AxiosError } from "axios";

import ConsultorioAdminPanel from "../src/pages/ConsultorioAdminPanel";
import * as consultorioService from "../src/services/consultorioService";

vi.mock("../src/services/consultorioService", () => ({
  actualizarModuloConsultorio: vi.fn(), actualizarReglaConsultorio: vi.fn(),
  crearInvitacionConsultorio: vi.fn(), crearModuloExtraordinario: vi.fn(),
  crearReglaConsultorio: vi.fn(), enviarInvitacionConsultorio: vi.fn(),
  listarConsultoriosAdministrados: vi.fn(), listarInvitacionesConsultorio: vi.fn(),
  listarModulosConsultorio: vi.fn(), listarProfesionalesConsultorio: vi.fn(),
  listarReglasConsultorio: vi.fn(), listarSalasConsultorio: vi.fn(),
  revocarInvitacionConsultorio: vi.fn(), suspenderModuloConsultorio: vi.fn(),
}));

const consultorio = { id: 4, nombre: "Consultorio E2E", zona_horaria: "America/Argentina/Buenos_Aires", duracion_modulo_minutos: 240, horizonte_materializacion_dias: 90, estado: "activo" };
const sala = { id: 8, consultorio_id: 4, nombre: "Sala E2E", codigo: "A", estado: "activa" };
const profesional = { profesional_id: 12, nombre: "Valentina E2E", estado: "activo" as const };
const regla = { id: 9, sala_id: 8, sala_nombre: "Sala E2E", profesional_id: 12, profesional_nombre: "Valentina E2E", invitacion_pendiente: false, dia_semana: 0, hora_inicio: "09:00:00", duracion_minutos: 240, zona_horaria: consultorio.zona_horaria, vigente_desde: "2026-10-19", vigente_hasta: null, estado: "activa" };
const ocurrencia = { id: 10, sala_id: 8, sala_nombre: "Sala E2E", profesional_id: null, profesional_nombre: "Invitación pendiente", fecha_inicio: "2026-10-19T12:00:00Z", fecha_fin: "2026-10-19T16:00:00Z", fecha_origen: "2026-10-19", estado: "activa" as const, origen: "recurrente" as const, patient_name: "No mostrar Paciente" } as never;

function prepararServicios() {
  vi.mocked(consultorioService.listarConsultoriosAdministrados).mockResolvedValue([consultorio]);
  vi.mocked(consultorioService.listarSalasConsultorio).mockResolvedValue([sala]);
  vi.mocked(consultorioService.listarProfesionalesConsultorio).mockResolvedValue([profesional]);
  vi.mocked(consultorioService.listarReglasConsultorio).mockResolvedValue([regla]);
  vi.mocked(consultorioService.listarModulosConsultorio).mockResolvedValue([ocurrencia]);
  vi.mocked(consultorioService.listarInvitacionesConsultorio).mockResolvedValue([]);
  vi.mocked(consultorioService.crearInvitacionConsultorio).mockResolvedValue({ id: 33, email: "profesional.sintetica@example.test", nombre_visible: null, estado: "preparacion", vence_en: "2026-10-22T00:00:00Z", modulos_reservados: 4 });
  vi.mocked(consultorioService.actualizarReglaConsultorio).mockResolvedValue({});
}

function renderizar() {
  render(<ConsultorioAdminPanel nombre="Valentina" onVolver={vi.fn()} onCerrarSesion={vi.fn()} />);
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.setSystemTime(new Date("2026-10-15T12:00:00Z"));
  prepararServicios();
});
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });

describe("panel administrativo de Consultorio", () => {
  it("muestra la ocupación pendiente sin datos clínicos y permite navegar semanas", async () => {
    renderizar();
    expect(await screen.findByRole("heading", { name: "Consultorio E2E" })).toBeInTheDocument();
    expect(screen.getByText("Invitación pendiente")).toBeInTheDocument();
    expect(screen.queryByText("No mostrar Paciente")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Semana siguiente" }));
    await waitFor(() => expect(consultorioService.listarModulosConsultorio).toHaveBeenCalledTimes(2));
    expect(screen.getByRole("navigation", { name: "Secciones de administración" })).toBeInTheDocument();
  });

  it("prepara una invitación con módulo semanal sin mostrar enlaces ni tokens", async () => {
    renderizar();
    await screen.findByRole("option", { name: "Sala E2E" });
    fireEvent.click(await screen.findByRole("button", { name: "Invitaciones" }));
    fireEvent.change(screen.getByLabelText("Correo electrónico"), { target: { value: "profesional.sintetica@example.test" } });
    fireEvent.change(screen.getByLabelText("Desde"), { target: { value: "2026-10-16" } });
    const submit = screen.getByRole("button", { name: "Preparar invitación" });
    const formulario = submit.closest("form") as HTMLFormElement;
    expect(Array.from(formulario.elements).filter((item) => (item as HTMLInputElement).willValidate && !(item as HTMLInputElement).validity.valid).map((item) => ({ type: (item as HTMLInputElement).type, value: (item as HTMLInputElement).value, required: (item as HTMLInputElement).required, min: (item as HTMLInputElement).min }))).toEqual([]);
    fireEvent.click(submit);
    await waitFor(() => expect(consultorioService.crearInvitacionConsultorio).toHaveBeenCalledTimes(1));
    const [, payload] = vi.mocked(consultorioService.crearInvitacionConsultorio).mock.calls[0];
    expect(payload).toMatchObject({ email: "profesional.sintetica@example.test", modulos: [{ sala_id: 8, dia_semana: 0, hora_inicio: "09:00", duracion_minutos: 240, vigente_desde: "2026-10-16" }] });
    expect(await screen.findByRole("status")).toHaveTextContent("La invitación quedó preparada");
    expect(screen.queryByText(/token|#token=/i)).not.toBeInTheDocument();
  });

  it("cuando backend bloquea un cambio sólo presenta el conteo de turnos", async () => {
    const error = new AxiosError("Conflict");
    Object.assign(error, { response: { data: { detail: { mensaje: "No mostrar detalles", turnos_afectados: 2 } }, status: 409, statusText: "Conflict", headers: {}, config: {} } });
    vi.mocked(consultorioService.actualizarReglaConsultorio).mockRejectedValue(error);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    renderizar();
    await screen.findByRole("option", { name: "Sala E2E" });
    fireEvent.click(await screen.findByRole("button", { name: "Módulos" }));
    fireEvent.click(screen.getByRole("button", { name: "Cambiar desde una fecha" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar cambio" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("afecta a 2 turnos");
    expect(screen.getByRole("alert")).not.toHaveTextContent("No mostrar detalles");
  });
});
