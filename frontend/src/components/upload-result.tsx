"use client";

import { Download, CheckCircle2 } from "lucide-react";
import type { AccExportMeta } from "@/lib/pmg-categories";

export function UploadResult({
  totalLancamentos,
  extratosOk,
  extratosErro,
  saldoDivergente = 0,
  onDownload,
  empresaNome,
}: {
  totalLancamentos: number;
  extratosOk: number;
  extratosErro: number;
  saldoDivergente?: number;
  onDownload: () => void;
  empresaNome: string;
}) {
  return (
    <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-6">
      <div className="flex items-start gap-3">
        <CheckCircle2 className="mt-0.5 text-emerald-600" size={22} />
        <div className="flex-1">
          <h3 className="font-semibold text-emerald-900">Processamento concluído</h3>
          <p className="mt-1 text-sm text-emerald-800">
            {extratosOk} extrato(s) processado(s) para <strong>{empresaNome}</strong>
            {extratosErro > 0 && ` · ${extratosErro} com erro`}
            {" · "}
            {totalLancamentos} lançamento(s) extraído(s)
            {saldoDivergente > 0 && (
              <>
                {" · "}
                <span className="text-amber-800">
                  {saldoDivergente} extrato(s) com divergência de saldo — revise no Dashboard
                </span>
              </>
            )}
          </p>

          {totalLancamentos > 0 && (
            <button
              type="button"
              onClick={onDownload}
              className="mt-4 flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700"
            >
              <Download size={18} />
              Baixar Fluxo de Caixa Consolidado (.xlsx)
            </button>
          )}

          <p className="mt-3 text-xs text-emerald-700">
            Planilha padrão ACC: PMG + Fluxo de Caixa Aprovado + Resumo por Banco
          </p>
        </div>
      </div>
    </div>
  );
}

export function buildExportFilename(empresaNome: string) {
  const slug = empresaNome
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  return `fluxo_caixa_acc_${slug}_${date}.xlsx`;
}

export function buildPeriodoLabel(dates: string[]): string {
  if (!dates.length) return new Date().toISOString().slice(0, 7);
  const sorted = [...dates].sort();
  const min = sorted[0].slice(0, 7);
  const max = sorted[sorted.length - 1].slice(0, 7);
  return min === max ? min : `${min} a ${max}`;
}

export type { AccExportMeta };
