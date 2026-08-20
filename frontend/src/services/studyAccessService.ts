import axios from "axios";
import type { PublicStudyRequest } from "../types/paciente";

const baseURL = import.meta.env.VITE_API_URL?.trim() ?? "http://127.0.0.1:8000";
const publicApi = axios.create({ baseURL, headers: { "Content-Type": "application/json" } });
export async function obtenerStudyRequestPublica(token: string): Promise<PublicStudyRequest> {
  return (await publicApi.get<PublicStudyRequest>("/public/study-requests/access", { params: { token } })).data;
}
export async function crearPublicStudyUploadIntent(token: string, file: File) { return (await publicApi.post<{ document_id: number; upload_url: string; expires_in_seconds: number; required_content_type: string }>("/public/study-requests/upload-intents", { token, filename: file.name, mime_type: file.type, size_bytes: file.size })).data; }
export async function subirAStorage(url: string, file: File, contentType: string) { const response = await fetch(url, { method: "PUT", headers: { "Content-Type": contentType }, body: file }); if (!response.ok) throw new Error("upload"); }
export async function confirmarPublicStudyDocumento(token: string, documentId: number) { return publicApi.post(`/public/study-requests/documents/${documentId}/confirm`, { token }); }
export async function removerPublicStudyDocumento(token: string, documentId: number) { return publicApi.post(`/public/study-requests/documents/${documentId}/remove`, { token }); }
export async function finalizarPublicStudy(token: string) { return (await publicApi.post<{ status: string; documents: Array<{ document_id: number; filename: string; size_bytes: number }> }>("/public/study-requests/submit", { token })).data; }
