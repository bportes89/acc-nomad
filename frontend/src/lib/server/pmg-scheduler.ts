import { formatUserError } from "@/lib/format-api-error";
import { calcularPmg } from "@/lib/pmg";
import type { Lancamento, PmgResumo, TesourariaLancamento } from "@/lib/types";
import { enviarPmg, PmgDeliveryError } from "@/lib/server/pmg-delivery";
import { getSupabaseAdmin } from "@/lib/server/supabase-admin";

interface AgendamentoRow {
  id: string;
  empresa_id: string;
  canal: "email" | "whatsapp";
  destinatario: string;
  dia_semana: number;
  ativo: boolean;
  empresas: { nome: string } | { nome: string }[] | null;
}

function empresaNome(ag: AgendamentoRow): string {
  if (!ag.empresas) return "Empresa";
  if (Array.isArray(ag.empresas)) return ag.empresas[0]?.nome ?? "Empresa";
  return ag.empresas.nome ?? "Empresa";
}

function previousMonthPeriod(reference = new Date()) {
  const ref = new Date(reference.getFullYear(), reference.getMonth(), 1);
  ref.setMonth(ref.getMonth() - 1);
  const year = ref.getFullYear();
  const month = ref.getMonth() + 1;
  const periodo = `${year}-${String(month).padStart(2, "0")}`;
  const inicio = `${periodo}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const fim = `${periodo}-${String(lastDay).padStart(2, "0")}`;
  return { periodo, inicio, fim };
}

function periodBounds(periodo: string) {
  const [year, month] = periodo.split("-").map(Number);
  const inicio = `${periodo}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const fim = `${periodo}-${String(lastDay).padStart(2, "0")}`;
  return { periodo, inicio, fim };
}

async function fetchActiveAgendamentos(diaSemana?: number) {
  const supabase = getSupabaseAdmin();
  let query = supabase
    .from("pmg_agendamentos")
    .select("id, empresa_id, canal, destinatario, dia_semana, ativo, empresas(nome)")
    .eq("ativo", true);

  if (diaSemana !== undefined) {
    query = query.eq("dia_semana", diaSemana);
  }

  const { data, error } = await query;
  if (error) throw new Error(formatUserError(error.message, "Erro ao buscar agendamentos."));
  return (data ?? []) as AgendamentoRow[];
}

async function alreadySentThisWeek(empresaId: string, canal: string): Promise<boolean> {
  const supabase = getSupabaseAdmin();
  const weekAgo = new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString();
  const { data } = await supabase
    .from("envios_pmg")
    .select("id")
    .eq("empresa_id", empresaId)
    .eq("canal", canal)
    .eq("status", "enviado")
    .gte("created_at", weekAgo);

  return (data?.length ?? 0) > 0;
}

async function fetchPmgData(empresaId: string, inicio: string, fim: string) {
  const supabase = getSupabaseAdmin();
  const [lancamentos, tesouraria] = await Promise.all([
    supabase
      .from("lancamentos")
      .select("valor, natureza, categoria, categoria_corrigida, data")
      .eq("empresa_id", empresaId)
      .gte("data", inicio)
      .lte("data", fim),
    supabase
      .from("tesouraria_lancamentos")
      .select("valor, natureza, categoria, data")
      .eq("empresa_id", empresaId)
      .gte("data", inicio)
      .lte("data", fim),
  ]);

  if (lancamentos.error) {
    throw new Error(formatUserError(lancamentos.error.message, "Erro ao buscar lançamentos."));
  }
  if (tesouraria.error) {
    throw new Error(formatUserError(tesouraria.error.message, "Erro ao buscar tesouraria."));
  }

  return {
    lancamentos: (lancamentos.data ?? []) as Lancamento[],
    tesouraria: (tesouraria.data ?? []) as TesourariaLancamento[],
  };
}

export async function runWeeklyPmgDispatch(options?: {
  force?: boolean;
  periodo?: string;
}) {
  const force = options?.force ?? false;
  const today = new Date();
  const weekday = today.getDay() === 0 ? 6 : today.getDay() - 1; // seg=0 … dom=6

  const agendamentos = force
    ? await fetchActiveAgendamentos()
    : await fetchActiveAgendamentos(weekday);

  const { periodo, inicio, fim } = options?.periodo
    ? periodBounds(options.periodo)
    : previousMonthPeriod(today);
  const supabase = getSupabaseAdmin();

  const enviados: Array<{ empresa: string; destinatario: string; canal: string; periodo: string }> =
    [];
  const erros: Array<{ empresa: string; destinatario: string; erro: string }> = [];
  const ignorados: Array<{ empresa_id: string; motivo: string }> = [];

  for (const ag of agendamentos) {
    const empresaNomeVal = empresaNome(ag);

    if (!force && (await alreadySentThisWeek(ag.empresa_id, ag.canal))) {
      ignorados.push({
        empresa_id: ag.empresa_id,
        motivo: "Já enviado nos últimos 7 dias",
      });
      continue;
    }

    const { lancamentos, tesouraria } = await fetchPmgData(ag.empresa_id, inicio, fim);
    if (!lancamentos.length && !tesouraria.length) {
      ignorados.push({
        empresa_id: ag.empresa_id,
        motivo: `Sem lançamentos em ${periodo}`,
      });
      continue;
    }

    const resumo: PmgResumo = calcularPmg(lancamentos, tesouraria);

    try {
      await enviarPmg({
        empresa_id: ag.empresa_id,
        empresa_nome: empresaNomeVal,
        periodo,
        periodo_inicio: inicio,
        periodo_fim: fim,
        canal: ag.canal,
        destinatario: ag.destinatario,
        resumo,
        enviado_por: null,
      });

      await supabase
        .from("pmg_agendamentos")
        .update({ ultimo_envio_em: new Date().toISOString() })
        .eq("id", ag.id);

      enviados.push({
        empresa: empresaNomeVal,
        destinatario: ag.destinatario,
        canal: ag.canal,
        periodo,
      });
    } catch (err) {
      const message = err instanceof PmgDeliveryError ? err.message : String(err);
      erros.push({
        empresa: empresaNomeVal,
        destinatario: ag.destinatario,
        erro: message,
      });
    }
  }

  return {
    periodo,
    dia_semana: weekday,
    total_agendamentos: agendamentos.length,
    enviados,
    erros,
    ignorados,
  };
}
