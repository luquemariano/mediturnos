import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../src/api/api", () => ({ default: { get: vi.fn(), post: vi.fn() } }));
import api from "../src/api/api";
import NotificationCenter from "../src/components/NotificationCenter";

const get = vi.mocked(api.get);
const post = vi.mocked(api.post);

describe("NotificationCenter", () => {
  beforeEach(() => { get.mockReset(); post.mockReset(); post.mockResolvedValue({ data: {} } as never); });

  it("mantiene estado normal sin unread", async () => {
    get.mockResolvedValue({ data: { items: [], unread_count: 0 } } as never);
    render(<NotificationCenter />);
    const button = await screen.findByRole("button", { name: "Notificaciones" });
    expect(button).not.toHaveClass("notification-trigger-alerta");
    expect(button).not.toHaveTextContent("1");
  });

  it("muestra alerta, badge y vuelve a normal al marcar leída", async () => {
    get.mockResolvedValue({ data: { items: [{ id: 4, type: "study_results_submitted", title: "Resultados", message: "Paciente QA envió resultados de Estudio QA Turnelia", entity_type: "study_request", entity_id: 8, read_at: null, created_at: "2026-08-20T18:07:00Z" }], unread_count: 1 } } as never);
    const onOpen = vi.fn();
    render(<NotificationCenter onOpen={onOpen} />);
    const button = await screen.findByRole("button", { name: "Notificaciones, 1 sin leer" });
    expect(button).toHaveClass("notification-trigger-alerta");
    expect(button).toHaveTextContent("1");
    fireEvent.click(button);
    fireEvent.click(await screen.findByRole("button", { name: /Paciente QA envió resultados/ }));
    await waitFor(() => expect(button).not.toHaveClass("notification-trigger-alerta"));
    expect(button).not.toHaveTextContent("1");
    expect(post).toHaveBeenCalledWith("/notifications/4/read");
    expect(onOpen).toHaveBeenCalledWith(expect.objectContaining({ entity_type: "study_request", entity_id: 8 }));
  });
});
