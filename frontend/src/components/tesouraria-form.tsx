"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { formatUserError } from "@/lib/format-api-error";
import { createClient } from "@/lib/supabase/client";
import type { Empresa, PlanoConta } from "@/lib/types";

export function TesourariaForm({
  empresas,
  planoContas,
}: {
  empresas: Empresa[];
  planoContas: PlanoConta[];
}) {
  const router = useRouter();
  const [empresaId, setEmpresaId] = useState(empresas[0]?.id ?? "");
  const [data, setData] = useState(new Date().toISOString().slice(0, 10));
  const [descricao, setDescricao] = useState("");
  const [valor, setValor] = useState("");
  const [natureza, setNatureza] = useState<"credito" | "debito">("credito");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const empresa = empresas.find((e) => e.id === empresaId);

  const categorias = useMemo(() => {
    if (!empresa) return [];
    return planoContas.filter((c) => c.segmento === empresa.segmento);
  }, [planoContas, empresa]);

  const [categoria, setCategoria] = useState(
    () => categorias.find((c) => c.categoria_pai === "receita")?.nome ?? categorias[0]?.nome ?? "",
  );

  function handleEmpresaChange(id: string) {
    setEmpresaId(id);
    const emp = empresas.find((e) => e.id === id);
    if (!emp) return;
    const cats = planoContas.filter((c) => c.segmento === emp.segmento);
    const defaultCat =
      cats.find((c) => c.categoria_pai === "receita")?.nome ?? cats[0]?.nome ?? "";
    setCategoria(defaultCat);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!empresaId || !descricao || !valor || !categoria) return;

    setLoading(true);
    setMessage("");

    const supabase = createClient();
    const { error } = await supabase.from("tesouraria_lancamentos").insert({
      empresa_id: empresaId,
      data,
      descricao,
      valor: parseFloat(valor.replace(",", ".")),
      natureza,
      categoria,
      origem: "TESOURARIA",
    });

    if (error) {
      setMessage(formatUserError(error.message, "Erro ao registrar lançamento."));
    } else {
      setDescricao("");
      setValor("");
      setMessage("Lançamento de tesouraria registrado!");
      router.refresh();
    }

    setLoading(false);
  }

  if (!empresas.length) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-amber-800">
        Nenhuma empresa vinculada.{" "}
        <Link href="/empresas" className="font-semibold underline">
          Cadastre uma empresa
        </Link>
        .
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
    >
      <h2 className="mb-4 font-semibold text-slate-900">Novo lançamento em espécie</h2>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Empresa
          </label>
          <select
            value={empresaId}
            onChange={(e) => handleEmpresaChange(e.target.value)}
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
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Data
          </label>
          <input
            type="date"
            value={data}
            onChange={(e) => setData(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            required
          />
        </div>
        <div className="sm:col-span-2">
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Descrição
          </label>
          <input
            type="text"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            placeholder="Ex: Venda em dinheiro no balcão"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Valor (R$)
          </label>
          <input
            type="text"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            placeholder="200.00"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Natureza
          </label>
          <select
            value={natureza}
            onChange={(e) => setNatureza(e.target.value as "credito" | "debito")}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="credito">Entrada (crédito)</option>
            <option value="debito">Saída (débito / troco)</option>
          </select>
        </div>
        <div className="sm:col-span-2">
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Categoria (plano de contas)
          </label>
          <select
            value={categoria}
            onChange={(e) => setCategoria(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            required
          >
            {categorias.map((c) => (
              <option key={c.id} value={c.nome}>
                {c.nome}
              </option>
            ))}
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="mt-6 w-full rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
      >
        {loading ? "Salvando…" : "Registrar tesouraria"}
      </button>

      {message && (
        <p className="mt-4 text-center text-sm text-slate-600">{message}</p>
      )}
    </form>
  );
}
