import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ReservaOnlinePanel from "./ReservaOnlinePanel";
import * as servicio from "../services/reservaOnlineService";

vi.mock("../services/reservaOnlineService");

const config = { reserva_online_activa: true, slug_publico: "sofia-r", url_publica: "https://turnelia.com.ar/reservar/sofia-r", especialidades: [], prestaciones: [{ identificador_publico: "pub-1", nombre: "Consulta", activa: true, habilitada_online: true, duracion_minutos: 30, modalidad: "presencial" }] };

describe("ReservaOnlinePanel", () => {
  beforeEach(() => { vi.clearAllMocks(); vi.mocked(servicio.obtenerReservaOnline).mockResolvedValue(config); vi.mocked(servicio.actualizarReservaOnline).mockResolvedValue(config); vi.mocked(servicio.actualizarHabilitacionOnline).mockResolvedValue(config.prestaciones[0]); Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: vi.fn().mockResolvedValue(undefined) } }); });

  it("muestra loading y configuración", async () => { vi.mocked(servicio.obtenerReservaOnline).mockReturnValue(new Promise(() => {})); render(<ReservaOnlinePanel />); expect(screen.getByText("Cargando configuración de reserva online…")).toBeInTheDocument(); });
  it("muestra enlace, prestación y abre página pública correctamente", async () => { render(<ReservaOnlinePanel />); expect(await screen.findByText("Consulta")).toBeInTheDocument(); expect(screen.getByText("30 min · presencial")).toBeInTheDocument(); const link=screen.getByRole("link",{name:"Ver página pública"}); expect(link).toHaveAttribute("href",config.url_publica); expect(link).toHaveAttribute("target","_blank"); expect(link).toHaveAttribute("rel","noopener noreferrer"); });
  it("activa/desactiva principal y copia enlace", async () => { render(<ReservaOnlinePanel />); const toggle=await screen.findByRole("button",{name:"Activadas"}); fireEvent.click(toggle); await waitFor(()=>expect(servicio.actualizarReservaOnline).toHaveBeenCalledWith(false)); fireEvent.click(screen.getByRole("button",{name:"Copiar enlace"})); await waitFor(()=>expect(navigator.clipboard.writeText).toHaveBeenCalledWith(config.url_publica)); expect(await screen.findByText("Enlace copiado")).toBeInTheDocument(); });
  it("habilita y deshabilita prestación por identificador público", async () => { render(<ReservaOnlinePanel />); const toggle=await screen.findByRole("button",{name:"Reserva online para Consulta"}); fireEvent.click(toggle); await waitFor(()=>expect(servicio.actualizarHabilitacionOnline).toHaveBeenCalledWith("pub-1",false)); });
  it("deshabilita prestación inactiva y muestra explicación", async () => { vi.mocked(servicio.obtenerReservaOnline).mockResolvedValue({...config, prestaciones:[{...config.prestaciones[0],activa:false,habilitada_online:false}]}); render(<ReservaOnlinePanel />); expect(await screen.findByText("Activá esta prestación antes de ofrecerla online.")).toBeInTheDocument(); expect(screen.getByRole("button",{name:"Reserva online para Consulta"})).toBeDisabled(); });
  it("muestra aviso sin prestaciones online y errores recuperables", async () => { vi.mocked(servicio.obtenerReservaOnline).mockResolvedValue({...config,prestaciones:config.prestaciones.map(p=>({...p,habilitada_online:false}))}); render(<ReservaOnlinePanel />); expect(await screen.findByText(/Tu página pública está activa/)).toBeInTheDocument(); vi.mocked(servicio.obtenerReservaOnline).mockRejectedValueOnce(new Error("fallo")); });
});
