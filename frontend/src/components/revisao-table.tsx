"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { Lancamento, PlanoConta, SegmentoEmpresa } from "@/lib/types";

function categoriasParaSegmento(
  categorias: PlanoConta[],
  segmento: SegmentoEmpresa | undefined,
): string[] {
  const filtradas = segmento
    ? categorias.filter((c) => c.segmento === segmento)
    : categorias;

  return [
    ...new Set([
      ...filtradas.map((c) => c.nome),
      "Não classificado (fallback)",
      "Sem categoria",
    ]),
  ];
}

export function RevisaoTable({
  lancamentos,
  categorias,
  segmentoPorEmpresa,
}: {
  lancamentos: Lancamento[];
  categorias: PlanoConta[];
  segmentoPorEmpresa: Record<string, SegmentoEmpresa>;
}) {
  const router = useRouter();
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Record<string, string>>({});

  const opcoesPorEmpresa = useMemo(() => {
    const map = new Map<string, string[]>();
    for (const l of lancamentos) {
      if (!map.has(l.empresa_id)) {
        map.set(
          l.empresa_id,
          categoriasParaSegmento(categorias, segmentoPorEmpresa[l.empresa_id]),
        );
      }
    }
    return map;
  }, [lancamentos, categorias, segmentoPorEmpresa]);

  async function salvar(l: Lancamento, acao: "confirmar" | "corrigir") {
    setLoadingId(l.id);
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    const opcoes = opcoesPorEmpresa.get(l.empresa_id) ?? [];
    const categoriaNova =
      selected[l.id] || l.categoria_corrigida || l.categoria || opcoes[0];

    await supabase
      .from("lancamentos")
      .update({ revisado: true, categoria_corrigida: categoriaNova })
      .eq("id", l.id);

    if (user) {
      await supabase.from("revisoes").insert({
        lancamento_id: l.id,
        revisor_id: user.id,
        acao,
        categoria_anterior: l.categoria,
        categoria_nova: categoriaNova,
      });
    }

    const { count: pendentes } = await supabase
      .from("lancamentos")
      .select("*", { count: "exact", head: true })
      .eq("extrato_id", l.extrato_id)
      .eq("revisado", false);

    if (pendentes === 0) {
      await supabase
        .from("extratos")
        .update({ status: "revisado" })
        .eq("id", l.extrato_id);
    }

    setLoadingId(null);
    router.refresh();
  }

  if (!lancamentos.length) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-500">
        Nenhum lançamento pendente de revisão.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[800px] text-sm">
        <thead className="bg-slate-50 text-left text-slate-600">
          <tr>
            <th className="px-4 py-3 font-medium">Data</th>
            <th className="px-4 py-3 font-medium">Descrição</th>
            <th className="px-4 py-3 font-medium">Valor</th>
            <th className="px-4 py-3 font-medium">Categoria IA</th>
            <th className="px-4 py-3 font-medium">Corrigir para</th>
            <th className="px-4 py-3 font-medium">Ações</th>
          </tr>
        </thead>
        <tbody>
          {lancamentos.map((l) => {
            const opcoes = opcoesPorEmpresa.get(l.empresa_id) ?? [];
            const atual =
              selected[l.id] ?? l.categoria_corrigida ?? l.categoria ?? opcoes[0];
            const mudou = atual !== (l.categoria ?? "");

            return (
              <tr key={l.id} className="border-t border-slate-100">
                <td className="px-4 py-3 whitespace-nowrap">{formatDate(l.data)}</td>
                <td className="px-4 py-3 max-w-xs truncate" title={l.descricao}>
                  {l.descricao}
                </td>
                <td
                  className={`px-4 py-3 font-medium whitespace-nowrap ${l.natureza === "credito" ? "text-emerald-600" : "text-red-600"}`}
                >
                  {l.natureza === "debito" ? "-" : "+"}
                  {formatCurrency(l.valor)}
                </td>
                <td className="px-4 py-3">{l.categoria ?? "—"}</td>
                <td className="px-4 py-3">
                  <select
                    value={atual}
                    onChange={(e) =>
                      setSelected((s) => ({ ...s, [l.id]: e.target.value }))
                    }
                    className="w-full min-w-[160px] rounded-md border border-slate-300 px-2 py-1 text-xs"
                  >
                    {opcoes.map((o) => (
                      <option key={o} value={o}>
                        {o}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3 whitespace-nowrap space-x-2">
                  <button
                    onClick={() => salvar(l, mudou ? "corrigir" : "confirmar")}
                    disabled={loadingId === l.id}
                    className="rounded-md bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {mudou ? "Corrigir" : "Confirmar"}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
