import { createClient } from "@/lib/supabase/server";
import { RevisaoTable } from "@/components/revisao-table";
import type { Lancamento, PlanoConta, SegmentoEmpresa } from "@/lib/types";

type LancamentoComEmpresa = Lancamento & {
  empresas: { segmento: SegmentoEmpresa } | null;
};

export default async function RevisaoPage() {
  const supabase = await createClient();

  const [{ data: lancamentos }, { data: categorias }] = await Promise.all([
    supabase
      .from("lancamentos")
      .select("*, empresas(segmento)")
      .eq("revisado", false)
      .order("data", { ascending: true })
      .limit(100),
    supabase.from("plano_contas").select("*").eq("ativo", true).order("ordem"),
  ]);

  const segmentoPorEmpresa: Record<string, SegmentoEmpresa> = {};
  for (const l of (lancamentos as LancamentoComEmpresa[] | null) ?? []) {
    if (l.empresas?.segmento) {
      segmentoPorEmpresa[l.empresa_id] = l.empresas.segmento;
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Revisão humana</h1>
      <p className="mt-1 text-slate-500">
        Confirme ou corrija as classificações sugeridas pela IA (feedback loop)
      </p>

      <div className="mt-8">
        <RevisaoTable
          lancamentos={(lancamentos as Lancamento[]) ?? []}
          categorias={(categorias as PlanoConta[]) ?? []}
          segmentoPorEmpresa={segmentoPorEmpresa}
        />
      </div>
    </div>
  );
}
