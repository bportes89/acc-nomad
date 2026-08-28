import { formatCurrency } from "@/lib/utils";
import type { Extrato } from "@/lib/types";

export function SaldoValidacaoBadge({ extrato }: { extrato: Extrato }) {
  if (extrato.status !== "processado" && extrato.status !== "revisado") {
    return null;
  }

  if (extrato.validacao_saldo_ok === null || extrato.validacao_saldo_ok === undefined) {
    return (
      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
        Saldo não validado
      </span>
    );
  }

  const warnings = extrato.validacao_detalhes?.warnings ?? [];

  if (extrato.validacao_saldo_ok) {
    return (
      <span
        className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700"
        title={warnings.join("\n") || "Saldos compatíveis com o extrato"}
      >
        Saldo OK
      </span>
    );
  }

  const delta = extrato.validacao_detalhes?.delta;
  const title =
    warnings.join("\n") ||
    (delta != null ? `Divergência de R$ ${Math.abs(delta).toFixed(2)}` : "Divergência de saldo");

  return (
    <span
      className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800"
      title={title}
    >
      Saldo divergente
    </span>
  );
}

export function SaldoValidacaoDetalhe({ extrato }: { extrato: Extrato }) {
  const d = extrato.validacao_detalhes;
  if (!d || (extrato.validacao_saldo_ok === null && !d.saldo_calculado)) {
    return null;
  }

  return (
    <div className="mt-1 space-y-0.5 text-xs text-slate-500">
      {d.saldo_inicial != null && (
        <div>Saldo inicial: {formatCurrency(d.saldo_inicial)}</div>
      )}
      {d.saldo_calculado != null && (
        <div>Saldo calculado: {formatCurrency(d.saldo_calculado)}</div>
      )}
      {d.saldo_final != null && (
        <div>Saldo final (PDF): {formatCurrency(d.saldo_final)}</div>
      )}
      {d.delta != null && Math.abs(d.delta) > 0.02 && (
        <div className="text-amber-700">Δ {formatCurrency(Math.abs(d.delta))}</div>
      )}
    </div>
  );
}
