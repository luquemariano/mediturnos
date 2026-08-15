export const LANDING_ASSETS = {
  dashboard: "/landing/dashboard.webp",
  dashboardMobile: "/landing/dashboard-mobile.webp",
  pacientes: "/landing/pacientes.webp",
  disponibilidad: "/landing/disponibilidad.webp",
  prestaciones: "/landing/prestaciones.webp",
  login: "/landing/login.webp",
  loginMobile: "/landing/login-mobile.webp",
  loginSecurity: "/landing/login.webp",
} as const;

export const WHATSAPP_URL = "";

export const PLANES = [
  {
    nombre: "Profesional",
    estado: "Disponible",
    descripcion: "Para profesionales que gestionan su propia consulta.",
    precio: "$34.900 / mes",
    accion: "Comenzar",
    href: "/registro",
    destacado: true,
    incluye: ["1 profesional", "Pacientes ilimitados*", "Agenda profesional", "Historia clínica y evoluciones", "Disponibilidad", "Prestaciones", "Perfil profesional", "Acceso multidispositivo", "Soporte"],
  },
  {
    nombre: "Consultorio",
    estado: "Consultar",
    descripcion: "Para consultorios pequeños que trabajan con varios profesionales.",
    precio: "$69.900 / mes",
    accion: "Consultar",
    href: "#contacto",
    incluye: ["Hasta 3 profesionales", "1 usuario administrativo incluido", "Pacientes ilimitados*", "Todo lo del plan Profesional", "Agendas independientes por profesional", "Gestión de profesionales", "Permisos por usuario", "Reportes básicos", "Soporte prioritario"],
    destacado: false,
  },
  {
    nombre: "Centro",
    estado: "Consultar",
    descripcion: "Para centros con varios profesionales y gestión centralizada.",
    precio: "$149.900 / mes",
    accion: "Consultar",
    href: "#contacto",
    incluye: ["Hasta 8 profesionales", "Hasta 3 usuarios administrativos incluidos", "Pacientes ilimitados*", "Todo lo del plan Consultorio", "Gestión centralizada", "Roles y permisos avanzados", "Gestión de múltiples agendas", "Reportes avanzados", "Soporte prioritario"],
    destacado: false,
  },
] as const;
