import { formatCurrency } from "@/lib/utils";
import type { PmgResumo } from "@/lib/types";

export function PmgChart({ resumo }: { resumo: PmgResumo }) {
  const items = [
    { label: "Receita", value: resumo.receita, color: "bg-emerald-500" },
    { label: "Custo Variável", value: resumo.custo_variavel, color: "bg-orange-500" },
    { label: "Custo Fixo", value: resumo.custo_fixo, color: "bg-blue-500" },
    { label: "Juros", value: resumo.juros, color: "bg-red-500" },
    { label: "Investimentos", value: resumo.investimentos, color: "bg-purple-500" },
  ];

  const max = Math.max(...items.map((i) => i.value), 1);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-6 text-lg font-semibold text-slate-900">
        Painel de Metas Gerenciais
      </h3>
      <div className="space-y-4">
        {items.map((item) => (
          <div key={item.label}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="text-slate-600">{item.label}</span>
              <span className="font-semibold text-slate-900">
                {formatCurrency(item.value)}
              </span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${item.color}`}
                style={{ width: `${(item.value / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6 rounded-lg bg-slate-50 p-4">
        <p className="text-sm text-slate-600">Resultado</p>
        <p className="text-2xl font-bold text-slate-900">
          {formatCurrency(
            resumo.receita -
              resumo.custo_variavel -
              resumo.custo_fixo -
              resumo.juros -
              resumo.investimentos,
          )}
        </p>
      </div>
    </div>
  );
}
