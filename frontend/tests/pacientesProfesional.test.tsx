import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Pacientes from "../src/components/Pacientes";
import * as servicio from "../src/services/pacienteService";

vi.mock("../src/services/pacienteService");
const props={nombre:"Dra. Ada",onVolver:vi.fn(),onAbrirAgenda:vi.fn(),onAbrirDisponibilidad:vi.fn(),onAbrirPrestaciones:vi.fn(),onAbrirPerfil:vi.fn(),onCerrarSesion:vi.fn()};
const paciente={id:1,nombre:"Ana",apellido:"López",dni:null,telefono:null,email:null,fecha_nacimiento:null};

describe("Pacientes profesional",()=>{
  beforeEach(()=>{vi.clearAllMocks();vi.mocked(servicio.buscarPacientesProfesional).mockResolvedValue([]);vi.mocked(servicio.obtenerEvolucionesPaciente).mockResolvedValue([])});
  it("muestra loading y vacío",async()=>{render(<Pacientes {...props}/>);expect(screen.getByText("Cargando pacientes...")).toBeInTheDocument();expect(await screen.findByText("No hay pacientes para mostrar.")).toBeInTheDocument()});
  it("lista, busca y abre detalle con historial",async()=>{vi.mocked(servicio.buscarPacientesProfesional).mockResolvedValue([paciente]);vi.mocked(servicio.obtenerHistorialPaciente).mockResolvedValue([]);render(<Pacientes {...props}/>);expect(await screen.findByText("Ana López")).toBeInTheDocument();fireEvent.change(screen.getByLabelText("Buscar pacientes"),{target:{value:"Ana"}});await waitFor(()=>expect(servicio.buscarPacientesProfesional).toHaveBeenLastCalledWith("Ana"));fireEvent.click(screen.getByText("Ver paciente"));expect(await screen.findByText("Historial de turnos")).toBeInTheDocument()});
  it("bloquea doble submit durante el alta",async()=>{let resolver:(v:any)=>void=()=>{};vi.mocked(servicio.crearPacienteProfesional).mockReturnValue(new Promise(r=>{resolver=r}));render(<Pacientes {...props}/>);await screen.findByText("No hay pacientes para mostrar.");fireEvent.click(screen.getByText("Nuevo paciente"));fireEvent.change(screen.getByLabelText("Nombre *"),{target:{value:"Ana"}});fireEvent.change(screen.getByLabelText("Apellido *"),{target:{value:"López"}});fireEvent.click(screen.getByText("Crear paciente"));expect(screen.getByText("Creando…")).toBeDisabled();expect(servicio.crearPacienteProfesional).toHaveBeenCalledTimes(1);resolver({});});
  it("renderiza historial de evoluciones",async()=>{vi.mocked(servicio.buscarPacientesProfesional).mockResolvedValue([paciente]);vi.mocked(servicio.obtenerHistorialPaciente).mockResolvedValue([]);vi.mocked(servicio.obtenerEvolucionesPaciente).mockResolvedValue([{id:3,paciente_id:1,profesional_id:2,profesional_nombre:"Dra. Ada",contenido:"Control clínico sin novedades.",created_at:"2026-08-15T13:00:00Z"}]);render(<Pacientes {...props}/>);fireEvent.click(await screen.findByText("Ver paciente"));expect(await screen.findByText("Control clínico sin novedades.")).toBeInTheDocument();expect(screen.getByText("15/08/2026 · 10:00")).toBeInTheDocument();expect(screen.getAllByText("Dra. Ada")).toHaveLength(2)});
  it("muestra estado vacío y abre el formulario",async()=>{vi.mocked(servicio.buscarPacientesProfesional).mockResolvedValue([paciente]);vi.mocked(servicio.obtenerHistorialPaciente).mockResolvedValue([]);render(<Pacientes {...props}/>);fireEvent.click(await screen.findByText("Ver paciente"));expect(await screen.findByText("Todavía no hay evoluciones registradas para este paciente.")).toBeInTheDocument();fireEvent.click(screen.getByText("Crear la primera evolución"));expect(screen.getByLabelText("Nueva evolución")).toBeInTheDocument()});
  it("guarda una evolución y evita doble envío",async()=>{
    vi.mocked(servicio.buscarPacientesProfesional).mockResolvedValue([paciente]);
    vi.mocked(servicio.obtenerHistorialPaciente).mockResolvedValue([]);
    vi.mocked(servicio.crearEvolucionPaciente).mockResolvedValue({id:4,paciente_id:1,profesional_id:2,profesional_nombre:"Dra. Ada",contenido:"Nueva nota",created_at:"2026-08-15T13:00:00Z"});
    render(<Pacientes {...props}/>);
    fireEvent.click(await screen.findByText("Ver paciente"));
    fireEvent.click(await screen.findByText("Crear la primera evolución"));
    fireEvent.change(screen.getByLabelText("Nueva evolución"),{target:{value:"Nueva nota"}});
    const guardar=screen.getByText("Guardar");
    fireEvent.click(guardar);
    fireEvent.click(guardar);
    await waitFor(()=>expect(servicio.crearEvolucionPaciente).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("Nueva nota")).toBeInTheDocument();
  });
  it("conserva el texto cuando falla la API",async()=>{vi.mocked(servicio.buscarPacientesProfesional).mockResolvedValue([paciente]);vi.mocked(servicio.obtenerHistorialPaciente).mockResolvedValue([]);vi.mocked(servicio.crearEvolucionPaciente).mockRejectedValue(new Error("fallo"));render(<Pacientes {...props}/>);fireEvent.click(await screen.findByText("Ver paciente"));fireEvent.click(await screen.findByText("Crear la primera evolución"));fireEvent.change(screen.getByLabelText("Nueva evolución"),{target:{value:"Texto que no debe perderse"}});fireEvent.click(screen.getByText("Guardar"));expect(await screen.findByRole("alert")).toHaveTextContent("Ocurrió un error inesperado.");expect(screen.getByLabelText("Nueva evolución")).toHaveValue("Texto que no debe perderse")});
});
