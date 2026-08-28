export const DIAS_SEMANA = [
  { value: 0, label: "Segunda-feira" },
  { value: 1, label: "Terça-feira" },
  { value: 2, label: "Quarta-feira" },
  { value: 3, label: "Quinta-feira" },
  { value: 4, label: "Sexta-feira" },
  { value: 5, label: "Sábado" },
  { value: 6, label: "Domingo" },
] as const;

export function diaSemanaLabel(dia: number): string {
  return DIAS_SEMANA.find((d) => d.value === dia)?.label ?? `Dia ${dia}`;
}
