import type { ReactNode } from "react";

import "./ProfesionalShell.css";
import Icono from "./Icono";

type SeccionProfesional = "inicio" | "agenda" | "pacientes" | "disponibilidad" | "prestaciones" | "perfil";

type ProfesionalShellProps = {
  activo: SeccionProfesional;
  nombre: string;
  tituloTopbar: string;
  children: ReactNode;
  onAbrirInicio: () => void;
  onAbrirAgenda: () => void;
  onAbrirPacientes: () => void;
  onAbrirDisponibilidad: () => void;
  onAbrirPrestaciones: () => void;
  onAbrirPerfil: () => void;
  onCerrarSesion: () => void;
  accionTopbar?: ReactNode;
};

export default function ProfesionalShell({
  activo,
  nombre,
  tituloTopbar,
  children,
  onAbrirInicio,
  onAbrirAgenda,
  onAbrirPacientes,
  onAbrirDisponibilidad,
  onAbrirPrestaciones,
  onAbrirPerfil,
  onCerrarSesion,
  accionTopbar,
}: ProfesionalShellProps) {
  const iniciales = nombre.split(" ").slice(0, 2)
    .map((parte) => parte.charAt(0)).join("").toUpperCase();

  const items = [
    { id: "inicio" as const, texto: "Inicio", icono: "inicio" as const, accion: onAbrirInicio },
    { id: "agenda" as const, texto: "Mi agenda", icono: "agenda" as const, accion: onAbrirAgenda },
    { id: "pacientes" as const, texto: "Pacientes", icono: "usuario" as const, accion: onAbrirPacientes },
    { id: "disponibilidad" as const, texto: "Mi disponibilidad", icono: "reloj" as const, accion: onAbrirDisponibilidad },
    { id: "prestaciones" as const, texto: "Mis prestaciones", icono: "check" as const, accion: onAbrirPrestaciones },
    { id: "perfil" as const, texto: "Mi perfil", icono: "perfil" as const, accion: onAbrirPerfil },
  ];

  return <div className="prof-app-shell">
    <aside className="prof-sidebar">
      <div className="prof-marca">
        <img className="prof-marca-simbolo" src="/brand/mediturnos-symbol-dark.svg" alt="" aria-hidden="true" />
        <div><strong>Turnelia</strong><small>Agenda profesional</small></div>
      </div>
      <nav aria-label="Navegación profesional">
        {items.map((item) => <button
          key={item.id}
          className={activo === item.id ? "activo" : undefined}
          type="button"
          aria-current={activo === item.id ? "page" : undefined}
          onClick={item.accion}
        ><Icono nombre={item.icono} />{item.texto}</button>)}
      </nav>
      <div className="prof-sidebar-perfil">
        <span className="prof-avatar">{iniciales || "P"}</span>
        <div><strong>{nombre}</strong><small>Profesional</small></div>
        <button type="button" onClick={onCerrarSesion} aria-label="Cerrar sesión"><Icono nombre="salir" /></button>
      </div>
    </aside>

    <main className="prof-main">
      <header className="prof-topbar">
        <div className="prof-marca-movil"><img className="prof-marca-simbolo" src="/brand/mediturnos-symbol.svg" alt="" aria-hidden="true" /><strong>Turnelia</strong></div>
        <span className="prof-topbar-titulo">{tituloTopbar}</span>
        {accionTopbar}
        <button type="button" className="prof-avatar prof-avatar-movil" onClick={onAbrirPerfil} aria-label="Abrir mi perfil">{iniciales || "P"}</button>
      </header>
      {children}
    </main>

    <nav className="prof-nav-movil" aria-label="Navegación principal">
      {items.map((item) => <button
        key={item.id}
        className={activo === item.id ? "activo" : undefined}
        type="button"
        aria-current={activo === item.id ? "page" : undefined}
        onClick={item.accion}
      ><Icono nombre={item.icono} /><span>{item.id === "disponibilidad" ? "Disponibilidad" : item.texto.replace("Mi ", "")}</span></button>)}
    </nav>
  </div>;
}
