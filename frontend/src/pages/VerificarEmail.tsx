import { useEffect, useState } from "react";
import { verificarEmail } from "../services/authService";
import AuthBrand from "../components/AuthBrand";
import axios from "axios";

export default function VerificarEmail({ onLogin }: { onLogin: () => void }) {
  const [estado, setEstado] = useState<"verificando" | "verificado" | "invalido">("verificando");
  useEffect(() => { const token = new URLSearchParams(window.location.search).get("token"); if (!token) { setEstado("invalido"); return; } void verificarEmail(token).then(() => setEstado("verificado")).catch((error) => { if (axios.isAxiosError(error) && error.response?.status === 400) setEstado("invalido"); else setEstado("invalido"); }); }, []);
  const contenido = estado === "verificando" ? ["Confirmando tu correo", "Estamos validando el enlace de verificación…"] : estado === "verificado" ? ["Correo verificado", "Tu cuenta ya está activa. Podés iniciar sesión para continuar."] : ["Enlace no disponible", "El enlace no es válido, venció o ya fue utilizado. Podés solicitar otro desde el inicio de sesión."];
  return <main className="pagina-login"><div className="acceso-publico"><AuthBrand subtitulo="Cuenta segura"/><section className="tarjeta-login verificacion-email"><p className="acceso-etiqueta">Verificación de correo</p><h2>{contenido[0]}</h2><p className="verificacion-descripcion">{contenido[1]}</p>{estado !== "verificando" && <button type="button" onClick={onLogin}>Ir a iniciar sesión</button>}</section></div></main>;
}
