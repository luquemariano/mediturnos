import { useEffect, useState } from "react";
import axios from "axios";
import { obtenerStudyRequestPublica } from "../services/studyAccessService";
import type { PublicStudyRequest } from "../types/paciente";
import "./StudyUploadAccess.css";

export default function StudyUploadAccess() {
  const token = new URLSearchParams(window.location.search).get("token");
  const [item, setItem] = useState<PublicStudyRequest | null>(null);
  const [state, setState] = useState(token ? "loading" : "invalid");
  useEffect(() => { if (!token) return; let active = true; obtenerStudyRequestPublica(token).then((value) => { if (active) { setItem(value); setState("ready"); } }).catch((error) => { if (active) setState(axios.isAxiosError(error) && error.response?.status === 404 ? "invalid" : "error"); }); return () => { active = false; }; }, [token]);
  if (state === "loading") return <main className="study-access-page"><section className="study-access-card"><p>Cargando solicitud...</p></section></main>;
  if (state === "invalid") return <main className="study-access-page"><section className="study-access-card"><h1>Enlace no disponible</h1><p>Este enlace no es válido o ya no está disponible.</p></section></main>;
  if (state === "error") return <main className="study-access-page"><section className="study-access-card"><h1>No pudimos cargar la solicitud</h1><p>Intentá nuevamente más tarde.</p></section></main>;
  return <main className="study-access-page"><section className="study-access-card"><p className="study-access-eyebrow">Turnelia</p><h1>Solicitud de estudio</h1><dl><div><dt>Profesional</dt><dd>{item?.professional_name}</dd></div><div><dt>Estudio solicitado</dt><dd>{item?.title}</dd></div>{item?.instructions && <div><dt>Indicaciones</dt><dd>{item.instructions}</dd></div>}<div><dt>Fecha</dt><dd>{item && new Intl.DateTimeFormat("es-AR").format(new Date(item.requested_at))}</dd></div>{item?.expires_at && <div><dt>Vencimiento</dt><dd>{new Intl.DateTimeFormat("es-AR").format(new Date(item.expires_at))}</dd></div>}<div><dt>Estado</dt><dd>Pendiente</dd></div></dl><p className="study-access-preparation">La carga de resultados estará disponible en el siguiente paso de implementación.</p></section></main>;
}
