import axios from "axios";

import { manejarErrorDeApi } from "./manejoSesion";

const apiUrlConfigurada =
  import.meta.env.VITE_API_URL?.trim();

if (!apiUrlConfigurada && !import.meta.env.DEV) {
  throw new Error(
    "VITE_API_URL debe estar configurada para producción.",
  );
}

const api = axios.create({
  baseURL:
    apiUrlConfigurada
    ?? "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((configuracion) => {
  const token = localStorage.getItem("access_token");

  if (token) {
    configuracion.headers.Authorization =
      `Bearer ${token}`;
  }

  return configuracion;
});

api.interceptors.response.use(
  (respuesta) => respuesta,
  (error) => manejarErrorDeApi(error),
);

export default api;
