export const LANDING_ASSETS = {
  dashboard: "/landing/dashboard.webp",
  dashboardMobile: "/landing/dashboard-mobile.webp",
  pacientes: "/landing/pacientes.webp",
  disponibilidad: "/landing/disponibilidad.webp",
  prestaciones: "/landing/prestaciones.webp",
  login: "/landing/login.webp",
  loginMobile: "/landing/login-mobile.webp",
  loginSecurity: "/landing/login-security.webp",
} as const;

export const WHATSAPP_URL = "";

export const PLANES = [
  {
    nombre: "Profesional",
    estado: "Disponible",
    descripcion: "Para profesionales que gestionan su propia consulta.",
    detalle: "1 profesional",
    precio: "$-- / mes",
    accion: "Comenzar",
    href: "/login",
    destacado: true,
    incluye: ["Agenda", "Pacientes", "Disponibilidad", "Prestaciones", "Perfil profesional", "Acceso multidispositivo"],
  },
  {
    nombre: "Consultorio",
    estado: "Próximamente",
    descripcion: "Turnelia para profesionales que comparten consultorio.",
    precio: "$-- / mes",
    accion: "Próximamente",
    href: "",
    incluye: [],
    destacado: false,
  },
  {
    nombre: "Centro",
    estado: "Próximamente",
    descripcion: "Una futura propuesta para centros con múltiples profesionales.",
    precio: "$-- / mes",
    accion: "Consultar",
    href: "#contacto",
    incluye: [],
    destacado: false,
  },
] as const;
