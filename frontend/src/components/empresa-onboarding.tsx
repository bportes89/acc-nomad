"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, CheckCircle2, ChevronRight } from "lucide-react";
import { formatSupabaseError } from "@/lib/format-api-error";
import { createClient } from "@/lib/supabase/client";
import {
  SEGMENTOS,
  formatCnpj,
  normalizeCnpj,
  segmentoLabel,
} from "@/lib/segmentos";
import type { Empresa, PlanoConta, SegmentoEmpresa } from "@/lib/types";

type Step = 1 | 2 | 3;

export function EmpresaOnboarding({
  empresas,
  planoContas,
}: {
  empresas: Empresa[];
  planoContas: PlanoConta[];
}) {
  const router = useRouter();
  const [step, setStep] = useState<Step>(empresas.length ? 1 : 1);
  const [nome, setNome] = useState("");
  const [cnpj, setCnpj] = useState("");
  const [segmento, setSegmento] = useState<SegmentoEmpresa>("comercio");
  const [instrucao, setInstrucao] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [createdEmpresaId, setCreatedEmpresaId] = useState<string | null>(null);

  const categoriasSegmento = useMemo(
    () => planoContas.filter((c) => c.segmento === segmento),
    [planoContas, segmento],
  );

  async function criarEmpresa(e: React.FormEvent) {
    e.preventDefault();
    const cnpjDigits = normalizeCnpj(cnpj);
    if (!nome.trim() || cnpjDigits.length !== 14) {
      setMessage("Informe o nome e um CNPJ válido (14 dígitos).");
      return;
    }

    setLoading(true);
    setMessage("");

    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      setMessage("Sessão expirada. Faça login novamente.");
      setLoading(false);
      return;
    }

    const { data: empresa, error } = await supabase
      .from("empresas")
      .insert({
        nome: nome.trim(),
        cnpj: cnpjDigits,
        segmento,
        instrucao_personalizada: instrucao.trim() || null,
      })
      .select("id")
      .single();

    if (error || !empresa) {
      setMessage(formatSupabaseError(error?.message ?? "Erro ao criar empresa."));
      setLoading(false);
      return;
    }

    const { error: membroError } = await supabase.from("empresa_membros").insert({
      empresa_id: empresa.id,
      user_id: user.id,
    });

    if (membroError) {
      setMessage(formatSupabaseError(membroError.message));
      setLoading(false);
      return;
    }

    setCreatedEmpresaId(empresa.id);
    setStep(3);
    setLoading(false);
    router.refresh();
  }

  async function salvarInstrucao(e: React.FormEvent) {
    e.preventDefault();
    const empresaId = createdEmpresaId ?? empresas[0]?.id;
    if (!empresaId) return;

    setLoading(true);
    setMessage("");

    const supabase = createClient();
    const { error } = await supabase
      .from("empresas")
      .update({ instrucao_personalizada: instrucao.trim() || null })
      .eq("id", empresaId);

    if (error) {
      setMessage(formatSupabaseError(error.message));
    } else {
      setMessage("Instruções salvas!");
      router.refresh();
    }
    setLoading(false);
  }

  return (
    <div className="space-y-8">
      {empresas.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-6 py-4">
            <h2 className="font-semibold text-slate-900">Suas empresas</h2>
            <p className="mt-1 text-xs text-slate-500">
              Empresas vinculadas à sua conta
            </p>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Nome</th>
                <th className="px-4 py-3 font-medium">CNPJ</th>
                <th className="px-4 py-3 font-medium">Segmento</th>
                <th className="px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {empresas.map((e) => (
                <tr key={e.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">{e.nome}</td>
                  <td className="px-4 py-3">{formatCnpj(e.cnpj)}</td>
                  <td className="px-4 py-3">{segmentoLabel(e.segmento)}</td>
                  <td className="px-4 py-3">
                    <Link
                      href="/fornecedores"
                      className="text-xs text-emerald-600 hover:underline"
                    >
                      Fornecedores
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="grid gap-8 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-6 flex items-center gap-2 text-sm text-slate-500">
            <Building2 size={18} className="text-emerald-600" />
            <span>Passo {step} de 3 — Setup inicial</span>
          </div>

          {step === 1 && (
            <form onSubmit={(e) => { e.preventDefault(); setStep(2); }} className="space-y-4">
              <h2 className="text-lg font-semibold text-slate-900">Dados da empresa</h2>
              <p className="text-sm text-slate-500">
                Informe CNPJ e segmento para carregar o plano de contas ACC correto.
              </p>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Razão social / Nome
                </label>
                <input
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  placeholder="Ex: Loja ABC Ltda"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  required
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  CNPJ
                </label>
                <input
                  value={cnpj}
                  onChange={(e) => setCnpj(formatCnpj(e.target.value))}
                  placeholder="00.000.000/0001-00"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  required
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Segmento
                </label>
                <select
                  value={segmento}
                  onChange={(e) => setSegmento(e.target.value as SegmentoEmpresa)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  {SEGMENTOS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-slate-400">
                  {SEGMENTOS.find((s) => s.value === segmento)?.descricao}
                </p>
              </div>

              <button
                type="submit"
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700"
              >
                Próximo: instruções e plano
                <ChevronRight size={16} />
              </button>
            </form>
          )}

          {step === 2 && (
            <form onSubmit={criarEmpresa} className="space-y-4">
              <h2 className="text-lg font-semibold text-slate-900">
                Instruções personalizadas
              </h2>
              <p className="text-sm text-slate-500">
                Regras extras para a IA classificar lançamentos desta empresa (opcional).
              </p>

              <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
                <strong>{nome || "Nova empresa"}</strong>
                {" · "}
                {segmentoLabel(segmento)}
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">
                  Instrução para a IA
                </label>
                <textarea
                  value={instrucao}
                  onChange={(e) => setInstrucao(e.target.value)}
                  rows={5}
                  placeholder="Ex: Classificar PIX recebido de clientes como Receita de vendas. Fornecedor X sempre como Fornecedor / Revenda."
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Voltar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  {loading ? "Criando…" : "Criar empresa e vincular"}
                </button>
              </div>

              {message && (
                <p className="text-center text-sm text-red-600">{message}</p>
              )}
            </form>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="mt-0.5 text-emerald-600" size={22} />
                <div>
                  <h2 className="text-lg font-semibold text-emerald-900">
                    Empresa configurada!
                  </h2>
                  <p className="mt-1 text-sm text-emerald-800">
                    Plano de contas <strong>{segmentoLabel(segmento)}</strong> ativo.
                    Cadastre fornecedores e envie extratos.
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <Link
                  href="/fornecedores"
                  className="rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700"
                >
                  Cadastrar fornecedores
                </Link>
                <Link
                  href="/upload"
                  className="rounded-lg border border-emerald-600 px-4 py-2.5 text-sm font-semibold text-emerald-700 hover:bg-emerald-50"
                >
                  Enviar extratos
                </Link>
                <button
                  type="button"
                  onClick={() => {
                    setStep(1);
                    setNome("");
                    setCnpj("");
                    setInstrucao("");
                    setCreatedEmpresaId(null);
                  }}
                  className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cadastrar outra empresa
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-6 py-4">
            <h2 className="font-semibold text-slate-900">
              Plano de contas — {segmentoLabel(segmento)}
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Categorias usadas na classificação automática e na revisão humana
            </p>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Código</th>
                <th className="px-4 py-3 font-medium">Categoria</th>
                <th className="px-4 py-3 font-medium">Grupo PMG</th>
              </tr>
            </thead>
            <tbody>
              {categoriasSegmento.map((c) => (
                <tr key={c.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-mono text-xs">{c.codigo}</td>
                  <td className="px-4 py-3">{c.nome}</td>
                  <td className="px-4 py-3 text-slate-500">{c.categoria_pai ?? "—"}</td>
                </tr>
              ))}
              {!categoriasSegmento.length && (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-slate-400">
                    Nenhuma categoria encontrada para este segmento.
                    Execute a migration 005 no Supabase.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {empresas.length > 0 && step !== 3 && (
        <form
          onSubmit={salvarInstrucao}
          className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <h3 className="font-semibold text-slate-900">
            Atualizar instruções da empresa principal
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            Edite regras personalizadas para {empresas[0]?.nome}
          </p>
          <textarea
            value={instrucao || empresas[0]?.instrucao_personalizada || ""}
            onChange={(e) => setInstrucao(e.target.value)}
            rows={3}
            className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={loading}
            className="mt-4 rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-900 disabled:opacity-50"
          >
            Salvar instruções
          </button>
          {message && !message.includes("Erro") && (
            <p className="mt-2 text-sm text-emerald-600">{message}</p>
          )}
        </form>
      )}
    </div>
  );
}
