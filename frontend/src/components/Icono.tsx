type NombreIcono =
  | "inicio"
  | "agenda"
  | "reloj"
  | "perfil"
  | "salir"
  | "flecha"
  | "alerta"
  | "recargar"
  | "check"
  | "usuario"
  | "ayuda";

type IconoProps = {
  nombre: NombreIcono;
  className?: string;
};

const trazos: Record<NombreIcono, React.ReactNode> = {
  inicio: <><path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></>,
  agenda: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></>,
  reloj: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
  perfil: <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
  salir: <><path d="M10 5H5v14h5M14 8l4 4-4 4M9 12h9"/></>,
  flecha: <><path d="m9 18 6-6-6-6"/></>,
  alerta: <><path d="M10.3 3.7 2.6 18a2 2 0 0 0 1.8 3h15.2a2 2 0 0 0 1.8-3L13.7 3.7a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/></>,
  recargar: <><path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/></>,
  check: <><path d="m5 12 4 4L19 6"/></>,
  usuario: <><circle cx="9" cy="8" r="3"/><path d="M3 19a6 6 0 0 1 12 0M17 8h4M19 6v4"/></>,
  ayuda: <><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 4.2 1.8c-1.1.9-1.7 1.3-1.7 2.7M12 17h.01"/></>,
};

export default function Icono({ nombre, className }: IconoProps) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {trazos[nombre]}
    </svg>
  );
}
