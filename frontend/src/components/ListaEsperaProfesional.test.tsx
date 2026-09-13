import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ListaEsperaProfesional from "./ListaEsperaProfesional";
import * as service from "../services/waitlistService";
import * as pacientes from "../services/pacienteService";
import * as prestaciones from "../services/prestacionService";

vi.mock("../services/waitlistService");
vi.mock("../services/pacienteService");
vi.mock("../services/prestacionService");
vi.mock("./NotificationCenter", () => ({ default: () => null }));

describe("ListaEsperaProfesional", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(service.listarWaitlist).mockResolvedValue([]);
    vi.mocked(service.crearWaitlist).mockResolvedValue({} as never);
    vi.mocked(pacientes.obtenerPacientesParaProfesional).mockResolvedValue([{ id: 1, nombre: "Ana", apellido: "Pérez", dni: null, telefono: null, email: "ana@example.com", fecha_nacimiento: null }]);
    vi.mocked(prestaciones.obtenerMisPrestaciones).mockResolvedValue([{ id: 2, nombre: "Consulta", descripcion: null, duracion_minutos: 30, precio: 0, modalidad: "presencial", activa: true, profesional_id: 3, especialidad_id: 4 }]);
  });
  it("ofrece alta, valida el formulario y muestra estado vacío", async () => {
    render(<ListaEsperaProfesional nombre="Laura Gómez" onVolver={vi.fn()} onAbrirAgenda={vi.fn()} onAbrirPacientes={vi.fn()} onAbrirDisponibilidad={vi.fn()} onAbrirPrestaciones={vi.fn()} onAbrirPerfil={vi.fn()} onCerrarSesion={vi.fn()} />);
    expect(await screen.findByText("No hay personas en esta vista")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "Agregar a la lista" })[0]);
    fireEvent.change(screen.getByLabelText("Paciente *"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Prestación *"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Desde *"), { target: { value: "2026-09-15" } });
    fireEvent.change(screen.getByLabelText("Hasta *"), { target: { value: "2026-09-20" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Agregar a la lista" })[1]);
    await waitFor(() => expect(service.crearWaitlist).toHaveBeenCalledWith(expect.objectContaining({ paciente_id: 1, prestacion_id: 2, fecha_desde: "2026-09-15", fecha_hasta: "2026-09-20" })));
  });
});
