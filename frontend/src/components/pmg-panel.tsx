"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Download, Mail, MessageCircle } from "lucide-react";
import { PmgChart } from "@/components/pmg-chart";
import { calcularPmg, toExportRows } from "@/lib/pmg";
import { exportFluxoCaixaCsv } from "@/lib/export-csv";
import { exportFluxoCaixaXlsx } from "@/lib/export-xlsx";
import { createClient } from "@/lib/supabase/client";
import { formatApiError } from "@/lib/format-api-error";
import type { Empresa, EnvioPmg, Lancamento, TesourariaLancamento } from "@/lib/types";

export function PmgPanel({
  empresas,
  lancamentos,
  tesouraria,
  envios,
  whatsappDisponivel = false,
}: {
  empresas: Empresa[];
  lancamentos: Lancamento[];
  tesouraria: TesourariaLancamento[];
  envios: EnvioPmg[];
  whatsappDisponivel?: boolean;
}) {
  const [empresaId, setEmpresaId] = useState(empresas[0]?.id ?? "todas");
  const [mes, setMes] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });
  const [destinatario, setDestinatario] = useState("");
  const [canal, setCanal] = useState<"email" | "whatsapp">("email");
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState("");
  const router = useRouter();

  const empresaAtual = empresas.find((e) => e.id === empresaId);

  const filtrados = useMemo(() => {
    const filtraMes = (data: string) => data.startsWith(mes);
    const filtraEmpresa = (empresa_id: string) =>
      empresaId === "todas" || empresa_id === empresaId;

    return {
      lancamentos: lancamentos.filter(
        (l) => filtraEmpresa(l.empresa_id) && filtraMes(l.data),
      ),
      tesouraria: tesouraria.filter(
        (t) => filtraEmpresa(t.empresa_id) && filtraMes(t.data),
      ),
    };
  }, [lancamentos, tesouraria, empresaId, mes]);

  const resumo = calcularPmg(filtrados.lancamentos, filtrados.tesouraria);
  const exportRows = toExportRows(filtrados.lancamentos, filtrados.tesouraria);
  const suffix = mes.replace("-", "_");

  function handleExportCsv() {
    exportFluxoCaixaCsv(exportRows, `fluxo_caixa_aprovado_${suffix}.csv`);
  }

  function handleExportXlsx() {
    exportFluxoCaixaXlsx(
      exportRows,
      resumo,
      `fluxo_caixa_aprovado_${suffix}.xlsx`,
      {
        empresaNome: empresaAtual?.nome ?? "Consolidado",
        empresaCnpj: empresaAtual?.cnpj ?? "—",
        periodoLabel: mes,
        extratosProcessados: 0,
        totalLancamentos: exportRows.length,
      },
    );
  }

  async function handleEnviar() {
    if (empresaId === "todas" || !destinatario.trim()) {
      setMessage("Selecione uma empresa e informe o destinatário.");
      return;
    }

    setSending(true);
    setMessage("");

    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    const res = await fetch("/api/pmg/enviar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        empresa_id: empresaId,
        empresa_nome: empresaAtual?.nome ?? "Empresa",
        periodo: mes,
        canal,
        destinatario: destinatario.trim(),
        resumo,
        enviado_por: user?.id,
      }),
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setMessage(formatApiError(data.error ?? data.detail, "Erro ao enviar PMG"));
    } else {
      const idHint = data.provider_message_id
        ? ` (ID: ${data.provider_message_id})`
        : "";
      setMessage(`PMG enviado por ${canal} para ${data.destinatario ?? destinatario}${idHint}`);
      router.refresh();
    }
    setSending(false);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Empresa
          </label>
          <select
            value={empresaId}
            onChange={(e) => setEmpresaId(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="todas">Todas</option>
            {empresas.map((e) => (
              <option key={e.id} value={e.id}>
                {e.nome}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">
            Período
          </label>
          <input
            type="month"
            value={mes}
            onChange={(e) => setMes(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div className="flex items-end gap-2">
          <button
            onClick={handleExportCsv}
            disabled={!exportRows.length}
            className="flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
          >
            <Download size={16} />
            CSV
          </button>
          <button
            onClick={handleExportXlsx}
            disabled={!exportRows.length}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            <Download size={16} />
            Excel (.xlsx)
          </button>
        </div>
      </div>

      <div className="max-w-2xl">
        <PmgChart resumo={resumo} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 font-semibold text-slate-900">Enviar PMG</h3>
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              Canal
            </label>
            <select
              value={canal}
              onChange={(e) => setCanal(e.target.value as "email" | "whatsapp")}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="email">E-mail</option>
              <option value="whatsapp" disabled={!whatsappDisponivel}>
                WhatsApp{whatsappDisponivel ? "" : " (configurar depois)"}
              </option>
            </select>
            {!whatsappDisponivel && (
              <p className="mt-1 text-xs text-slate-500">
                WhatsApp será habilitado quando o cliente definir o provedor (Z-API, Evolution, etc.).
              </p>
            )}
          </div>
          <div className="sm:col-span-2">
            <label className="mb-1 block text-xs font-medium text-slate-600">
              {canal === "email" ? "E-mail destino" : "WhatsApp (5511999999999)"}
            </label>
            <input
              value={destinatario}
              onChange={(e) => setDestinatario(e.target.value)}
              placeholder={
                canal === "email" ? "cliente@empresa.com" : "5511999999999"
              }
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        </div>
        <button
          onClick={handleEnviar}
          disabled={sending || empresaId === "todas"}
          className="mt-4 flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {canal === "email" ? <Mail size={16} /> : <MessageCircle size={16} />}
          {sending ? "Enviando…" : "Enviar relatório"}
        </button>
        {message && (
          <p className="mt-3 text-sm text-slate-600">{message}</p>
        )}
        {empresaId === "todas" && (
          <p className="mt-2 text-xs text-amber-600">
            Selecione uma empresa específica para enviar.
          </p>
        )}
      </div>

      {envios.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-6 py-4">
            <h3 className="font-semibold text-slate-900">Histórico de envios</h3>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Data</th>
                <th className="px-4 py-3 font-medium">Canal</th>
                <th className="px-4 py-3 font-medium">Destinatário</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Rastreio</th>
              </tr>
            </thead>
            <tbody>
              {envios.slice(0, 10).map((e) => (
                <tr key={e.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">
                    {new Date(e.created_at).toLocaleDateString("pt-BR")}
                  </td>
                  <td className="px-4 py-3 capitalize">{e.canal}</td>
                  <td className="px-4 py-3">{e.destinatario}</td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        e.status === "enviado"
                          ? "text-emerald-600"
                          : "text-red-600"
                      }
                    >
                      {e.status}
                    </span>
                    {e.status === "erro" && e.erro_mensagem && (
                      <p className="mt-1 max-w-xs text-xs text-red-500" title={e.erro_mensagem}>
                        {e.erro_mensagem.slice(0, 80)}
                        {e.erro_mensagem.length > 80 ? "…" : ""}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {e.provider_message_id ? (
                      <span title={e.provider_message_id}>
                        {e.provider_name ?? "api"}:{" "}
                        {e.provider_message_id.length > 12
                          ? `${e.provider_message_id.slice(0, 12)}…`
                          : e.provider_message_id}
                      </span>
                    ) : e.canal === "whatsapp" ? (
                      "—"
                    ) : (
                      "e-mail"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-sm text-slate-500">
        {exportRows.length} lançamento(s) no período (banco + tesouraria).
      </p>
    </div>
  );
}
