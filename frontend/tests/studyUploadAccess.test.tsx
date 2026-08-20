import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
const service = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock("../src/services/studyAccessService", () => ({ obtenerStudyRequestPublica: service.get }));
import StudyUploadAccess from "../src/pages/StudyUploadAccess";

describe("StudyUploadAccess", () => {
  beforeEach(() => { vi.clearAllMocks(); window.history.replaceState({}, "", "/estudios/enviar?token=abc"); });
  it("muestra estado inválido sin token", async () => { window.history.replaceState({}, "", "/estudios/enviar"); render(<StudyUploadAccess />); expect(await screen.findByText("Enlace no disponible")).toBeInTheDocument(); expect(service.get).not.toHaveBeenCalled(); });
  it("muestra loading y solicitud válida sin shell", async () => { let resolve!: (value: unknown) => void; service.get.mockReturnValue(new Promise((r) => { resolve = r; })); render(<StudyUploadAccess />); expect(screen.getByText("Cargando solicitud...")).toBeInTheDocument(); resolve({ study_request_id: 1, professional_name: "Sofía Ramírez", title: "Hemograma", instructions: "En ayunas", requested_at: "2026-08-20T12:00:00Z", expires_at: null, status: "pending" }); await waitFor(() => expect(screen.getByText("Hemograma")).toBeInTheDocument()); expect(screen.queryByText("Iniciar sesión")).not.toBeInTheDocument(); expect(localStorage.getItem("access_token")).toBeNull(); });
  it("muestra error de red", async () => { service.get.mockRejectedValue(new Error("network")); render(<StudyUploadAccess />); expect(await screen.findByText("No pudimos cargar la solicitud")).toBeInTheDocument(); });
});
