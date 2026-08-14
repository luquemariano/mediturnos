import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Pacientes from "../src/components/Pacientes";
import * as servicio from "../src/services/pacienteService";

vi.mock("../src/services/pacienteService");
const props={nombre:"Dra. Ada",onVolver:vi.fn(),onAbrirAgenda:vi.fn(),onAbrirDisponibilidad:vi.fn(),onAbrirPrestaciones:vi.fn(),onAbrirPerfil:vi.fn(),onCerrarSesion:vi.fn()};

describe("Pacientes profesional",()=>{
  beforeEach(()=>{vi.clearAllMocks();vi.mocked(servicio.buscarPacientesProfesional).mockResolvedValue([])});
  it("muestra loading y vacío",async()=>{render(<Pacientes {...props}/>);expect(screen.getByText("Cargando pacientes...")).toBeInTheDocument();expect(await screen.findByText("No hay pacientes para mostrar.")).toBeInTheDocument()});
  it("lista, busca y abre detalle con historial",async()=>{vi.mocked(servicio.buscarPacientesProfesional).mockResolvedValue([{id:1,nombre:"Ana",apellido:"López",dni:"12345678",telefono:"123456",email:null,fecha_nacimiento:null}]);vi.mocked(servicio.obtenerHistorialPaciente).mockResolvedValue([]);render(<Pacientes {...props}/>);expect(await screen.findByText("Ana López")).toBeInTheDocument();fireEvent.change(screen.getByLabelText("Buscar pacientes"),{target:{value:"Ana"}});await waitFor(()=>expect(servicio.buscarPacientesProfesional).toHaveBeenLastCalledWith("Ana"));fireEvent.click(screen.getByText("Ver paciente"));expect(await screen.findByText("Historial de turnos")).toBeInTheDocument()});
  it("bloquea doble submit durante el alta",async()=>{let resolver:(v:any)=>void=()=>{};vi.mocked(servicio.crearPacienteProfesional).mockReturnValue(new Promise(r=>{resolver=r}));render(<Pacientes {...props}/>);await screen.findByText("No hay pacientes para mostrar.");fireEvent.click(screen.getByText("Nuevo paciente"));fireEvent.change(screen.getByLabelText("Nombre *"),{target:{value:"Ana"}});fireEvent.change(screen.getByLabelText("Apellido *"),{target:{value:"López"}});fireEvent.click(screen.getByText("Crear paciente"));expect(screen.getByText("Creando…")).toBeDisabled();expect(servicio.crearPacienteProfesional).toHaveBeenCalledTimes(1);resolver({});});
});
