import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import CampaniasAdmin from "../src/pages/CampaniasAdmin";

const { get, post } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));
vi.mock("../src/api/api", () => ({ default: { get, post, put: vi.fn() } }));

describe("CampaniasAdmin", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    get.mockImplementation((url: string, config?: { params?: { busqueda?: string } }) => Promise.resolve({ data: url.endsWith("novedades") ? [{ id: 1, titulo: "Nueva agenda", descripcion_corta: "Mejoras visuales", prioridad: "normal", cerrada: true, activa: true }] : config?.params?.busqueda ? [{ id: 11, nombre: "Dr. Bruno", email: "bruno@example.test" }] : [{ id: 10, nombre: "Dra. Ana", email: "ana@example.test" }, { id: 11, nombre: "Dr. Bruno", email: "bruno@example.test" }] }));
    post.mockImplementation((url: string) => Promise.resolve({ data: url === "/admin/campanias/preview" ? { asunto: "Novedades — Turnelia", html: "<p>Vista real</p>", texto: "Vista real", destinatarios: 1 } : url === "/admin/campanias" ? { id: 7 } : { enviadas: 1, fallidas: 0 } }));
    vi.stubGlobal("confirm", vi.fn(() => true));
  });

  it("previsualiza y exige confirmar para enviar la campaña", async () => {
    render(<CampaniasAdmin onVolver={vi.fn()} />);
    fireEvent.change(await screen.findByLabelText("Asunto"), { target: { value: "Novedades" } });
    fireEvent.change(screen.getByLabelText("Preheader"), { target: { value: "Actualizaciones" } });
    fireEvent.change(screen.getByLabelText("Mensaje principal"), { target: { value: "Hola profesionales" } });
    fireEvent.click(screen.getByLabelText(/Nueva agenda/));
    fireEvent.click(screen.getByRole("button", { name: "Vista previa del email" }));
    expect(await screen.findByTitle("Vista previa del email")).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith("/admin/campanias/preview", expect.objectContaining({ novedades_ids: [1] }));
    expect(post.mock.calls.some(([url]) => String(url).includes("/enviar"))).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Enviar ahora" }));
    await waitFor(() => expect(post).toHaveBeenCalledWith("/admin/campanias/7/enviar", { confirmar: true }));
    expect(window.confirm).toHaveBeenCalledOnce();
    expect(await screen.findByRole("status")).toHaveTextContent("1 entregas correctas");
  });

  it("conserva la selección manual al cambiar la búsqueda y envía el mismo conjunto contado", async () => {
    const { container } = render(<CampaniasAdmin onVolver={vi.fn()} />);
    fireEvent.click(await screen.findByRole("radio", { name: /Selección manual/ }));
    fireEvent.click(screen.getByLabelText(/Dra\. Ana/));
    fireEvent.change(screen.getByPlaceholderText("Nombre o email"), { target: { value: "Bruno" } });
    expect(await screen.findByLabelText(/Dr\. Bruno/)).toBeInTheDocument();
    expect(container.querySelector(".campanias-recipient-count strong")).toHaveTextContent("1");

    fireEvent.change(screen.getByLabelText("Asunto"), { target: { value: "Novedades" } });
    fireEvent.change(screen.getByLabelText("Preheader"), { target: { value: "Actualizaciones" } });
    fireEvent.change(screen.getByLabelText("Mensaje principal"), { target: { value: "Hola profesionales" } });
    fireEvent.click(screen.getByRole("button", { name: "Vista previa del email" }));
    expect(await screen.findByTitle("Vista previa del email")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Enviar ahora" }));
    await waitFor(() => expect(post).toHaveBeenCalledWith("/admin/campanias/7/enviar", { confirmar: true }));

    expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining("a 1 profesionales"));
    expect(post).toHaveBeenCalledWith("/admin/campanias", expect.objectContaining({ todos: false, destinatarios_ids: [10] }));
  });
});
