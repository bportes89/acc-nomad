"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Upload } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { formatApiError } from "@/lib/format-api-error";
import { processarExtratoNoBackend } from "@/lib/processar-extrato";
import {
  exportAccConsolidadoXlsx,
  lancamentosToAccRows,
} from "@/lib/acc-export";
import {
  UploadResult,
  buildExportFilename,
  buildPeriodoLabel,
} from "@/components/upload-result";
import type { Empresa, Lancamento } from "@/lib/types";

type ExtratoJoin = { banco: string | null; nome_arquivo: string };

export function UploadForm({ empresas }: { empresas: Empresa[] }) {
  const router = useRouter();
  const [empresaId, setEmpresaId] = useState(empresas[0]?.id ?? "");
  const [files, setFiles] = useState<FileList | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [batchExtratoIds, setBatchExtratoIds] = useState<string[]>([]);
  const [batchStats, setBatchStats] = useState({
    ok: 0,
    erro: 0,
    lancamentos: 0,
    saldoDivergente: 0,
  });

  const empresa = empresas.find((e) => e.id === empresaId);

  async function fetchAndDownloadXlsx(extratoIds: string[]) {
    if (!empresa || !extratoIds.length) return;

    const supabase = createClient();
    const { data: lancamentos } = await supabase
      .from("lancamentos")
      .select("*, extratos(banco, nome_arquivo)")
      .in("extrato_id", extratoIds)
      .order("data", { ascending: true });

    const rows = lancamentosToAccRows(
      (lancamentos as (Lancamento & { extratos?: ExtratoJoin | null })[]) ?? [],
    );

    if (!rows.length) return;

    const filename = buildExportFilename(empresa.nome);
    exportAccConsolidadoXlsx(rows, {
      empresaNome: empresa.nome,
      empresaCnpj: empresa.cnpj,
      periodoLabel: buildPeriodoLabel(rows.map((r) => r.data)),
      extratosProcessados: extratoIds.length,
      totalLancamentos: rows.length,
    }, filename);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!files?.length || !empresaId) return;

    setLoading(true);
    setMessage("");
    setBatchExtratoIds([]);
    setBatchStats({ ok: 0, erro: 0, lancamentos: 0, saldoDivergente: 0 });

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      setMessage("Sessão expirada. Faça login novamente.");
      setLoading(false);
      return;
    }

    const userId = session.user.id;

    const successIds: string[] = [];
    let ok = 0;
    let erro = 0;
    let totalLancamentos = 0;

    let saldoDivergente = 0;
    let lastError = "";

    for (const file of Array.from(files)) {
      const { data: extrato, error: extratoError } = await supabase
        .from("extratos")
        .insert({
          empresa_id: empresaId,
          nome_arquivo: file.name,
          status: "pendente",
          uploaded_by: userId,
        })
        .select("id")
        .single();

      if (extratoError || !extrato) {
        erro += 1;
        lastError = `Erro ao registrar extrato: ${extratoError?.message}`;
        setMessage(lastError);
        continue;
      }

      const formData = new FormData();
      formData.append("empresa_id", empresaId);
      formData.append("extrato_id", extrato.id);
      formData.append("nome_arquivo", file.name);
      formData.append("arquivo", file);

      if (empresa?.segmento) formData.append("segmento", empresa.segmento);
      if (empresa?.instrucao_personalizada) {
        formData.append("instrucao_personalizada", empresa.instrucao_personalizada);
      }

      let res: Response;
      try {
        res = await processarExtratoNoBackend(
          formData,
          session.access_token,
          setMessage,
        );
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Erro ao processar extrato";
        await supabase
          .from("extratos")
          .update({ status: "erro", erro_mensagem: msg })
          .eq("id", extrato.id);
        erro += 1;
        lastError = msg;
        setMessage(lastError);
        continue;
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = formatApiError(
          err.detail ?? err.error,
          `Erro ao processar extrato (HTTP ${res.status})`,
        );
        await supabase
          .from("extratos")
          .update({ status: "erro", erro_mensagem: String(detail) })
          .eq("id", extrato.id);
        erro += 1;
        lastError = detail;
        setMessage(lastError);
        continue;
      }

      const data = await res.json();
      ok += 1;
      successIds.push(extrato.id);
      totalLancamentos += data.transactions?.length ?? 0;
      if (data.saldo_validation && data.saldo_validation.ok === false) {
        saldoDivergente += 1;
      }
    }

    setBatchExtratoIds(successIds);
    setBatchStats({ ok, erro, lancamentos: totalLancamentos, saldoDivergente });

    if (ok > 0) {
      await fetchAndDownloadXlsx(successIds);
      setMessage("");
    } else {
      setMessage(lastError || "Nenhum extrato processado com sucesso.");
    }

    setFiles(null);
    setLoading(false);
    router.refresh();
  }

  if (!empresas.length) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-amber-800">
        Nenhuma empresa vinculada.{" "}
        <a href="/empresas" className="font-semibold underline">
          Cadastre uma empresa
        </a>{" "}
        para começar.
      </div>
    );
  }

  return (
    <div>
      <form
        onSubmit={handleSubmit}
        className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Empresa
          </label>
          <select
            value={empresaId}
            onChange={(e) => setEmpresaId(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {empresas.map((e) => (
              <option key={e.id} value={e.id}>
                {e.nome} — {e.cnpj}
              </option>
            ))}
          </select>
        </div>

        <div className="mb-6">
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Extratos PDF (múltiplos bancos)
          </label>
          <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-10">
            <Upload className="mb-2 text-slate-400" size={32} />
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={(e) => setFiles(e.target.files)}
              className="text-sm text-slate-600"
            />
            <p className="mt-2 text-xs text-slate-400">
              Selecione vários PDFs — serão consolidados em um único .xlsx ACC
            </p>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !files?.length}
          className="w-full rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {loading ? "Processando… (IA + PDF, aguarde)" : "Enviar, processar e baixar XLSX"}
        </button>

        {message && (
          <p className="mt-4 text-center text-sm text-red-600">{message}</p>
        )}
      </form>

      {batchStats.ok > 0 && (
        <UploadResult
          totalLancamentos={batchStats.lancamentos}
          extratosOk={batchStats.ok}
          extratosErro={batchStats.erro}
          saldoDivergente={batchStats.saldoDivergente}
          empresaNome={empresa?.nome ?? ""}
          onDownload={() => fetchAndDownloadXlsx(batchExtratoIds)}
        />
      )}
    </div>
  );
}
