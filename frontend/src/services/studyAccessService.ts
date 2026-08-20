import axios from "axios";
import type { PublicStudyRequest } from "../types/paciente";

const baseURL = import.meta.env.VITE_API_URL?.trim() ?? "http://127.0.0.1:8000";
const publicApi = axios.create({ baseURL, headers: { "Content-Type": "application/json" } });
export async function obtenerStudyRequestPublica(token: string): Promise<PublicStudyRequest> {
  return (await publicApi.get<PublicStudyRequest>("/public/study-requests/access", { params: { token } })).data;
}
