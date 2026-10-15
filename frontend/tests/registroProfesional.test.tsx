import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RegistroProfesional from "../src/components/RegistroProfesional";
import { rutaOnboarding } from "../src/utils/onboarding";

vi.mock("../src/api/api", () => ({ default: { get: vi.fn().mockImplementation((path: string) => Promise.resolve({ data: path === "/catalogo/actividades-profesionales" ? [
  { id: 1, codigo: "profesional_matriculable", nombre: "Profesión con matrícula", requiere_matricula: true, requiere_especialidad: true },
  { id: 2, codigo: "servicios_estetica", nombre: "Servicios de estética", requiere_matricula: false, requiere_especialidad: false },
] : [
  { id: 1, nombre: "Clínica", descripcion: null, duracion_turno_minutos: 30, activa: true },
  { id: 2, nombre: "Psicología", descripcion: null, duracion_turno_minutos: 45, activa: true },
] })), post: vi.fn() } }));
vi.mock("../src/services/authService", () => ({ registrarProfesional: vi.fn() }));
import { registrarProfesional } from "../src/services/authService";

describe("registro profesional", () => {
  beforeEach(() => vi.clearAllMocks());
  it("renderiza el formulario y carga especialidades", async () => {
    render(<RegistroProfesional onRegistrado={vi.fn()}/>);
    expect(screen.getByRole("heading", { name: "Creá tu cuenta" })).toBeInTheDocument();
    expect(await screen.findByRole("option", { name: "Profesión con matrícula" })).toBeInTheDocument();
  });
  it("persiste el resultado mediante el callback luego del registro", async () => {
    const resultado={access_token:"jwt",token_type:"bearer",usuario_id:1,usuario:"Ana Pérez",rol:"profesional",profesional_id:1,onboarding_step:"perfil" as const};
    vi.mocked(registrarProfesional).mockResolvedValue(resultado); const onRegistrado=vi.fn(); render(<RegistroProfesional onRegistrado={onRegistrado}/>);
    fireEvent.change(screen.getByLabelText("Nombre"),{target:{value:"Ana"}});fireEvent.change(screen.getByLabelText("Apellido"),{target:{value:"Pérez"}});fireEvent.change(screen.getByLabelText("Correo electrónico"),{target:{value:"ana@test.com"}});fireEvent.change(screen.getByLabelText(/Contraseña/),{target:{value:"secreto123"}});fireEvent.change(await screen.findByLabelText("Actividad profesional"),{target:{value:"1"}});fireEvent.change(screen.getByLabelText(/Matrícula/),{target:{value:"MP100"}});fireEvent.change(screen.getByLabelText(/Profesión \/ especialidad/),{target:{value:"1"}});fireEvent.click(screen.getByRole("button",{name:"Crear cuenta"}));
    await waitFor(()=>expect(onRegistrado).toHaveBeenCalledWith(resultado));
    expect(registrarProfesional).toHaveBeenCalledWith(expect.objectContaining({ actividad_profesional_id: 1, matricula: "MP100", especialidad_id: 1 }));
  });
  it("muestra las opciones formales ampliadas y no ofrece texto libre", async () => {
    render(<RegistroProfesional onRegistrado={vi.fn()}/>);
    fireEvent.change(await screen.findByLabelText("Actividad profesional"), {target:{value:"1"}});
    expect(await screen.findByRole("option", { name: "Psicología" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Otro" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Especificá tu profesión o especialidad")).not.toBeInTheDocument();
  });
  it("mantiene una ruta estable para cada paso",()=>{expect(rutaOnboarding("perfil")).toBe("/onboarding/perfil");expect(rutaOnboarding("prestaciones")).toBe("/onboarding/prestaciones");expect(rutaOnboarding("disponibilidad")).toBe("/onboarding/disponibilidad");expect(rutaOnboarding("listo")).toBe("/onboarding/listo");});

  it("oculta matrícula y especialidad para servicios de estética", async () => {
    vi.mocked(registrarProfesional).mockResolvedValue({access_token:"jwt",token_type:"bearer",usuario_id:2,usuario:"Eva Sol",rol:"profesional",profesional_id:2,onboarding_step:"perfil"});
    render(<RegistroProfesional onRegistrado={vi.fn()}/>);
    fireEvent.change(await screen.findByLabelText("Actividad profesional"), {target:{value:"2"}});
    expect(screen.queryByLabelText("Matrícula *")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Profesión / especialidad *")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("no requiere matrícula");
  });

  it("registra estética sin incluir matrícula ni especialidad en el payload", async () => {
    const resultado={access_token:"jwt",token_type:"bearer",usuario_id:2,usuario:"Eva Sol",rol:"profesional",profesional_id:2,onboarding_step:"perfil" as const};
    vi.mocked(registrarProfesional).mockResolvedValue(resultado);
    const onRegistrado=vi.fn(); render(<RegistroProfesional onRegistrado={onRegistrado}/>);
    fireEvent.change(screen.getByLabelText("Nombre"),{target:{value:"Eva"}});
    fireEvent.change(screen.getByLabelText("Apellido"),{target:{value:"Sol"}});
    fireEvent.change(screen.getByLabelText("Correo electrónico"),{target:{value:"eva@example.com"}});
    fireEvent.change(screen.getByLabelText(/Contraseña/),{target:{value:"secreto123"}});
    fireEvent.change(await screen.findByLabelText("Actividad profesional"),{target:{value:"2"}});
    fireEvent.click(screen.getByRole("button",{name:"Crear cuenta"}));
    await waitFor(()=>expect(onRegistrado).toHaveBeenCalledWith(resultado));
    expect(registrarProfesional).toHaveBeenCalledWith(expect.objectContaining({actividad_profesional_id:2}));
    expect(registrarProfesional).toHaveBeenCalledWith(expect.not.objectContaining({matricula: expect.anything(), especialidad_id: expect.anything()}));
  });
});
