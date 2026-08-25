export type PeriodoDia = "manana" | "tarde" | "noche";

export function minutosDesdeHora(valor: string): number {
  const [hora, minuto] = valor.split(":").map(Number);
  return hora * 60 + minuto;
}

export function periodoDesdeMinutos(minutos: number): PeriodoDia {
  if (minutos < 13 * 60) return "manana";
  if (minutos < 20 * 60) return "tarde";
  return "noche";
}

export function periodoDesdeHora(valor: string): PeriodoDia {
  return periodoDesdeMinutos(minutosDesdeHora(valor));
}

export function etiquetaPeriodo(periodo: PeriodoDia): "Mañana" | "Tarde" | "Noche" {
  const etiquetas = {
    manana: "Mañana",
    tarde: "Tarde",
    noche: "Noche",
  } as const;
  return etiquetas[periodo];
}
