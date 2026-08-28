"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CalendarClock, Play } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { DIAS_SEMANA, diaSemanaLabel } from "@/lib/pmg-schedule";
import type { Empresa, PmgAgendamento } from "@/lib/types";

export function PmgAgendamentoPanel({
  empresas,
  agendamentos: initial,
}: {
  empresas: Empresa[];
  agendamentos: PmgAgendamento[];
}) {
  const router = useRouter();
  const [empresaId, setEmpresaId] = useState(empresas[0]?.id ?? "");
  const [destinatario, setDestinatario] = useState("");
  const [canal, setCanal] = useState<"email" | "whatsapp">("email");
  const [diaSemana, setDiaSemana] = useState(0);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!empresaId || !destinatario.trim()) return;

    setLoading(true);
    setMessage("");

    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    const { error } = await supabase.from("pmg_agendamentos").insert({
      empresa_id: empresaId,
      destinatario: destinatario.trim(),
      canal,
      dia_semana: diaSemana,
      ativo: true,
      created_by: user?.id,
    });

    if (error) {
      setMessage(error.message);
    } else {
      setDestinatario("");
      setMessage("Agendamento semanal salvo!");
      router.refresh();
    }
    setLoading(false);
  }

  async function toggleAtivo(ag: PmgAgendamento) {
    const supabase = createClient();
    await supabase
      .from("pmg_agendamentos")
      .update({ ativo: !ag.ativo })
      .eq("id", ag.id);
    router.refresh();
  }

  async function remover(id: string) {
    if (!confirm("Remover agendamento semanal?")) return;
    const supabase = createClient();
    await supabase.from("pmg_agendamentos").delete().eq("id", id);
    router.refresh();
  }

  async function dispararAgora() {
    setLoading(true);
    setMessage("");
    const res = await fetch("/api/pmg/disparo-semanal?force=true", { method: "POST" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setMessage(data.error || data.detail || "Erro no disparo");
    } else {
      const ok = data.enviados?.length ?? 0;
      const erros = data.erros?.length ?? 0;
      setMessage(
        `Disparo concluído (${data.periodo}): ${ok} enviado(s), ${erros} erro(s).`,
      );
      router.refresh();
    }
    setLoading(false);
  }

  if (!empresas.length) {
    return null;
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="flex items-center gap-2 font-semibold text-slate-900">
            <CalendarClock size={18} />
            Envio semanal automático
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Toda semana, no dia escolhido, envia o PMG do <strong>mês anterior</strong> por
            e-mail ou WhatsApp (cron Vercel + Render).
          </p>
        </div>
        <button
          type="button"
          onClick={dispararAgora}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium hover:bg-slate-50 disabled:opacity-50"
        >
          <Play size={14} />
          Testar disparo agora
        </button>
      </div>

      <form onSubmit={salvar} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Empresa</label>
          <select
            value={empresaId}
            onChange={(e) => setEmpresaId(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {empresas.map((e) => (
              <option key={e.id} value={e.id}>
                {e.nome}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Dia da semana</label>
          <select
            value={diaSemana}
            onChange={(e) => setDiaSemana(Number(e.target.value))}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {DIAS_SEMANA.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Canal</label>
          <select
            value={canal}
            onChange={(e) => setCanal(e.target.value as "email" | "whatsapp")}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="email">E-mail</option>
            <option value="whatsapp">WhatsApp</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Destinatário</label>
          <input
            value={destinatario}
            onChange={(e) => setDestinatario(e.target.value)}
            placeholder={canal === "email" ? "cliente@empresa.com" : "5511999999999"}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            required
          />
        </div>
        <div className="sm:col-span-2 lg:col-span-4">
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {loading ? "Salvando…" : "Agendar envio semanal"}
          </button>
        </div>
      </form>

      {message && <p className="mt-3 text-sm text-slate-600">{message}</p>}

      {initial.length > 0 && (
        <table className="mt-6 w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-3 py-2 font-medium">Empresa</th>
              <th className="px-3 py-2 font-medium">Dia</th>
              <th className="px-3 py-2 font-medium">Canal</th>
              <th className="px-3 py-2 font-medium">Destinatário</th>
              <th className="px-3 py-2 font-medium">Último envio</th>
              <th className="px-3 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {initial.map((ag) => {
              const emp = empresas.find((e) => e.id === ag.empresa_id);
              return (
                <tr key={ag.id} className="border-t border-slate-100">
                  <td className="px-3 py-2">{emp?.nome ?? "—"}</td>
                  <td className="px-3 py-2">{diaSemanaLabel(ag.dia_semana)}</td>
                  <td className="px-3 py-2 capitalize">{ag.canal}</td>
                  <td className="px-3 py-2">{ag.destinatario}</td>
                  <td className="px-3 py-2 text-xs text-slate-500">
                    {ag.ultimo_envio_em
                      ? new Date(ag.ultimo_envio_em).toLocaleString("pt-BR")
                      : "—"}
                  </td>
                  <td className="px-3 py-2 space-x-2 whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => toggleAtivo(ag)}
                      className="text-xs text-emerald-600 hover:underline"
                    >
                      {ag.ativo ? "Pausar" : "Ativar"}
                    </button>
                    <button
                      type="button"
                      onClick={() => remover(ag.id)}
                      className="text-xs text-red-600 hover:underline"
                    >
                      Remover
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
