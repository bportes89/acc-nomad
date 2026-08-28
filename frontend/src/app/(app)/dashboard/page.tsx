import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { StatCard } from "@/components/stat-card";
import { ExtratoActions } from "@/components/extrato-actions";
import { ReportErroDialog } from "@/components/report-erro-dialog";
import { SaldoValidacaoBadge, SaldoValidacaoDetalhe } from "@/components/saldo-validacao-badge";
import { formatDate } from "@/lib/utils";
import type { Empresa, Extrato } from "@/lib/types";

export default async function DashboardPage() {
  const supabase = await createClient();

  const [{ data: extratos }, { data: empresas }] = await Promise.all([
    supabase
      .from("extratos")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(20),
    supabase.from("empresas").select("*"),
  ]);

  const { count: totalLancamentos } = await supabase
    .from("lancamentos")
    .select("*", { count: "exact", head: true });

  const { count: pendentesRevisao } = await supabase
    .from("lancamentos")
    .select("*", { count: "exact", head: true })
    .eq("revisado", false);

  const lista = (extratos as Extrato[] | null) ?? [];
  const empresasLista = (empresas as Empresa[] | null) ?? [];
  const processados = lista.filter((e) =>
    ["processado", "revisado"].includes(e.status),
  ).length;
  const comErro = lista.filter((e) => e.status === "erro").length;

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-1 text-slate-500">
            Visão geral do processamento de extratos
          </p>
        </div>
        <Link
          href="/suporte"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Reportar problema
        </Link>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Extratos OK" value={String(processados)} accent="green" />
        <StatCard label="Total lançamentos" value={String(totalLancamentos ?? 0)} accent="blue" />
        <StatCard label="Pendentes revisão" value={String(pendentesRevisao ?? 0)} accent="amber" />
        <StatCard label="Com erro" value={String(comErro)} accent="red" />
      </div>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-4">
          <h2 className="font-semibold text-slate-900">Extratos recentes</h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-6 py-3 font-medium">Arquivo</th>
              <th className="px-6 py-3 font-medium">Banco</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Saldo</th>
              <th className="px-6 py-3 font-medium">Lançamentos</th>
              <th className="px-6 py-3 font-medium">Data</th>
              <th className="px-6 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {lista.map((e) => (
              <tr key={e.id} className="border-t border-slate-100">
                <td className="px-6 py-3">
                  <div>{e.nome_arquivo}</div>
                  {e.erro_mensagem && (
                    <div className="mt-1 text-xs text-red-500">{e.erro_mensagem}</div>
                  )}
                </td>
                <td className="px-6 py-3 uppercase">{e.banco ?? "—"}</td>
                <td className="px-6 py-3">
                  <StatusBadge status={e.status} />
                </td>
                <td className="px-6 py-3">
                  <SaldoValidacaoBadge extrato={e} />
                  <SaldoValidacaoDetalhe extrato={e} />
                </td>
                <td className="px-6 py-3">{e.total_lancamentos}</td>
                <td className="px-6 py-3">{formatDate(e.created_at.slice(0, 10))}</td>
                <td className="px-6 py-3">
                  <div className="flex items-center gap-1">
                    <ReportErroDialog extrato={e} empresas={empresasLista} />
                    <ExtratoActions extrato={e} />
                  </div>
                </td>
              </tr>
            ))}
            {!lista.length && (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-slate-400">
                  Nenhum extrato ainda. Envie um PDF na aba Upload.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pendente: "bg-slate-100 text-slate-600",
    processando: "bg-blue-100 text-blue-700",
    processado: "bg-emerald-100 text-emerald-700",
    erro: "bg-red-100 text-red-700",
    revisado: "bg-purple-100 text-purple-700",
  };

  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status] ?? styles.pendente}`}
    >
      {status}
    </span>
  );
}
