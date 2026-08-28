import { createClient } from "@/lib/supabase/server";
import { PmgPanel } from "@/components/pmg-panel";
import { PmgAgendamentoPanel } from "@/components/pmg-agendamento-panel";
import { isWhatsAppConfigured } from "@/lib/server/whatsapp";
import type { Empresa, EnvioPmg, Lancamento, PmgAgendamento, TesourariaLancamento } from "@/lib/types";

export default async function PmgPage() {
  const supabase = await createClient();
  const whatsappDisponivel = isWhatsAppConfigured();

  const [
    { data: empresas },
    { data: lancamentos },
    { data: tesouraria },
    { data: envios },
    { data: agendamentos },
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
    supabase
      .from("pmg_agendamentos")
      .select("*")
      .order("created_at", { ascending: false }),
  ]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Relatório PMG</h1>
      <p className="mt-1 text-slate-500">
        Painel de Metas Gerenciais — exportação e envio por e-mail/WhatsApp
      </p>

      <div className="mt-8 space-y-8">
        <PmgAgendamentoPanel
          empresas={(empresas as Empresa[]) ?? []}
          agendamentos={(agendamentos as PmgAgendamento[]) ?? []}
          whatsappDisponivel={whatsappDisponivel}
        />
        <PmgPanel
          empresas={(empresas as Empresa[]) ?? []}
          lancamentos={(lancamentos as Lancamento[]) ?? []}
          tesouraria={(tesouraria as TesourariaLancamento[]) ?? []}
          envios={(envios as EnvioPmg[]) ?? []}
          whatsappDisponivel={whatsappDisponivel}
        />
      </div>
    </div>
  );
}
