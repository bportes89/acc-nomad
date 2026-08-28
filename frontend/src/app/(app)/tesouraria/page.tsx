import { createClient } from "@/lib/supabase/server";
import { TesourariaForm } from "@/components/tesouraria-form";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { Empresa, PlanoConta, TesourariaLancamento } from "@/lib/types";

export default async function TesourariaPage() {
  const supabase = await createClient();

  const [{ data: empresas }, { data: lancamentos }, { data: planoContas }] =
    await Promise.all([
      supabase.from("empresas").select("*"),
      supabase
        .from("tesouraria_lancamentos")
        .select("*")
        .order("data", { ascending: false })
        .limit(50),
      supabase.from("plano_contas").select("*").eq("ativo", true).order("ordem"),
    ]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Tesouraria</h1>
      <p className="mt-1 text-slate-500">
        Lançamentos em espécie (caixa físico) — origem TESOURARIA
      </p>

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <TesourariaForm
          empresas={(empresas as Empresa[]) ?? []}
          planoContas={(planoContas as PlanoConta[]) ?? []}
        />

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-6 py-4">
            <h2 className="font-semibold text-slate-900">Lançamentos recentes</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Data</th>
                <th className="px-4 py-3 font-medium">Descrição</th>
                <th className="px-4 py-3 font-medium">Valor</th>
              </tr>
            </thead>
            <tbody>
              {(lancamentos as TesourariaLancamento[] | null)?.map((l) => (
                <tr key={l.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">{formatDate(l.data)}</td>
                  <td className="px-4 py-3 max-w-xs truncate">{l.descricao}</td>
                  <td
                    className={`px-4 py-3 font-medium ${l.natureza === "credito" ? "text-emerald-600" : "text-red-600"}`}
                  >
                    {l.natureza === "debito" ? "-" : "+"}
                    {formatCurrency(l.valor)}
                  </td>
                </tr>
              )) ?? (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-slate-400">
                    Nenhum lançamento de tesouraria ainda.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
