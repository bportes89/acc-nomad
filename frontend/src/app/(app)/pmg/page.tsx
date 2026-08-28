import { createClient } from "@/lib/supabase/server";
import { PmgPanel } from "@/components/pmg-panel";
import type { Empresa, EnvioPmg, Lancamento, TesourariaLancamento } from "@/lib/types";

export default async function PmgPage() {
  const supabase = await createClient();

  const [
    { data: empresas },
    { data: lancamentos },
    { data: tesouraria },
    { data: envios },
  ] = await Promise.all([
    supabase.from("empresas").select("*"),
    supabase
      .from("lancamentos")
      .select("*")
      .eq("revisado", true)
      .order("data", { ascending: false }),
    supabase
      .from("tesouraria_lancamentos")
      .select("*")
      .order("data", { ascending: false }),
    supabase
      .from("envios_pmg")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(20),
  ]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Relatório PMG</h1>
      <p className="mt-1 text-slate-500">
        Painel de Metas Gerenciais — exportação e envio por e-mail/WhatsApp
      </p>

      <div className="mt-8">
        <PmgPanel
          empresas={(empresas as Empresa[]) ?? []}
          lancamentos={(lancamentos as Lancamento[]) ?? []}
          tesouraria={(tesouraria as TesourariaLancamento[]) ?? []}
          envios={(envios as EnvioPmg[]) ?? []}
        />
      </div>
    </div>
  );
}
