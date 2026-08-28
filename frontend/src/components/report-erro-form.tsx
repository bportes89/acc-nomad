"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { REPORT_CATEGORIAS, REPORT_STATUS_LABELS, reportStatusStyle } from "@/lib/reports";
import type { Empresa, Extrato, ReportErro, ReportErroCategoria } from "@/lib/types";

type ReportPrefill = {
  extratoId?: string;
  empresaId?: string;
  categoria?: ReportErroCategoria;
  titulo?: string;
  descricao?: string;
};

export function ReportErroForm({
  empresas,
  prefill,
  onSuccess,
  compact = false,
}: {
  empresas: Empresa[];
  prefill?: ReportPrefill;
  onSuccess?: () => void;
  compact?: boolean;
}) {
  const router = useRouter();
  const [empresaId, setEmpresaId] = useState(
    prefill?.empresaId ?? empresas[0]?.id ?? "",
  );
  const [extratoId] = useState(prefill?.extratoId ?? "");
  const [categoria, setCategoria] = useState<ReportErroCategoria>(
    prefill?.categoria ?? "outro",
  );
  const [titulo, setTitulo] = useState(prefill?.titulo ?? "");
  const [descricao, setDescricao] = useState(prefill?.descricao ?? "");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!titulo.trim() || !descricao.trim()) return;

    setLoading(true);
    setMessage("");
    setError("");

    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      setError("Sessão expirada. Faça login novamente.");
      setLoading(false);
      return;
    }

    const { error: insertError } = await supabase.from("reports_erro").insert({
      user_id: user.id,
      empresa_id: empresaId || null,
      extrato_id: extratoId || null,
      categoria,
      titulo: titulo.trim(),
      descricao: descricao.trim(),
    });

    if (insertError) {
      setError(insertError.message);
    } else {
      setMessage("Report enviado! Nossa equipe irá analisar.");
      if (!prefill) {
        setTitulo("");
        setDescricao("");
        setCategoria("outro");
      }
      onSuccess?.();
      router.refresh();
    }

    setLoading(false);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={
        compact
          ? "space-y-3"
          : "space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      }
    >
      {!compact && (
        <div>
          <h2 className="font-semibold text-slate-900">Abrir report de erro</h2>
          <p className="mt-1 text-xs text-slate-500">
            Descreva o problema — equivalente ao Ticketed Support da ACC
          </p>
        </div>
      )}

      {empresas.length > 0 && (
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Empresa (opcional)
          </label>
          <select
            value={empresaId}
            onChange={(e) => setEmpresaId(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">— Não informada —</option>
            {empresas.map((e) => (
              <option key={e.id} value={e.id}>
                {e.nome}
              </option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">
          Categoria
        </label>
        <select
          value={categoria}
          onChange={(e) => setCategoria(e.target.value as ReportErroCategoria)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          {REPORT_CATEGORIAS.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">
          Título
        </label>
        <input
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          placeholder="Ex: Extrato Bradesco não processou"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          required
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">
          Descrição
        </label>
        <textarea
          value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
          rows={compact ? 3 : 5}
          placeholder="Descreva o que aconteceu, qual arquivo, banco, mensagem de erro…"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          required
        />
      </div>

      {extratoId && (
        <p className="text-xs text-slate-400">
          Extrato vinculado: {extratoId.slice(0, 8)}…
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
      >
        {loading ? "Enviando…" : "Enviar report"}
      </button>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {message && <p className="text-sm text-emerald-700">{message}</p>}
    </form>
  );
}

export function buildExtratoReportPrefill(extrato: Extrato): ReportPrefill {
  return {
    extratoId: extrato.id,
    empresaId: extrato.empresa_id,
    categoria: "extrato",
    titulo: `Erro no extrato: ${extrato.nome_arquivo}`,
    descricao: [
      `Arquivo: ${extrato.nome_arquivo}`,
      extrato.banco ? `Banco: ${extrato.banco}` : null,
      extrato.erro_mensagem ? `Erro: ${extrato.erro_mensagem}` : null,
      "",
      "Descreva abaixo o que você esperava que acontecesse:",
    ]
      .filter(Boolean)
      .join("\n"),
  };
}

export function ReportsList({ reports }: { reports: ReportErro[] }) {
  if (!reports.length) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-slate-500">
        Nenhum report enviado ainda.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-6 py-4">
        <h2 className="font-semibold text-slate-900">Seus reports</h2>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-600">
          <tr>
            <th className="px-4 py-3 font-medium">Data</th>
            <th className="px-4 py-3 font-medium">Título</th>
            <th className="px-4 py-3 font-medium">Categoria</th>
            <th className="px-4 py-3 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((r) => (
            <tr key={r.id} className="border-t border-slate-100 align-top">
              <td className="px-4 py-3 whitespace-nowrap">
                {new Date(r.created_at).toLocaleDateString("pt-BR")}
              </td>
              <td className="px-4 py-3">
                <div className="font-medium text-slate-900">{r.titulo}</div>
                <div className="mt-1 text-xs text-slate-500 line-clamp-2">{r.descricao}</div>
                {r.resposta && (
                  <div className="mt-2 rounded bg-emerald-50 px-2 py-1 text-xs text-emerald-800">
                    Resposta: {r.resposta}
                  </div>
                )}
              </td>
              <td className="px-4 py-3 capitalize">{r.categoria}</td>
              <td className="px-4 py-3">
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${reportStatusStyle(r.status)}`}
                >
                  {REPORT_STATUS_LABELS[r.status] ?? r.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
