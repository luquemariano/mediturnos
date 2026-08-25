import api from "../api/api";
import type { CuentaActual } from "../types/cuenta";
export async function obtenerCuentaActual(): Promise<CuentaActual> {
  return (await api.get<CuentaActual>("/cuentas/me/actual")).data;
}
