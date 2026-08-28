export const REPORT_CATEGORIAS = [
  { value: "extrato", label: "Erro no processamento de extrato" },
  { value: "classificacao", label: "Classificação incorreta" },
  { value: "pmg", label: "PMG / relatório" },
  { value: "login", label: "Login / acesso" },
  { value: "outro", label: "Outro" },
] as const;

export const REPORT_STATUS_LABELS: Record<string, string> = {
  aberto: "Aberto",
  em_analise: "Em análise",
  resolvido: "Resolvido",
};

export function reportStatusStyle(status: string): string {
  const styles: Record<string, string> = {
    aberto: "bg-red-100 text-red-700",
    em_analise: "bg-amber-100 text-amber-700",
    resolvido: "bg-emerald-100 text-emerald-700",
  };
  return styles[status] ?? "bg-slate-100 text-slate-600";
}
