"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import type { Empresa, Fornecedor, PlanoConta } from "@/lib/types";

export function FornecedoresManager({
  empresas,
  fornecedores: initial,
  planoContas,
}: {
  empresas: Empresa[];
  fornecedores: Fornecedor[];
  planoContas: PlanoConta[];
}) {
  const router = useRouter();
  const [empresaId, setEmpresaId] = useState(empresas[0]?.id ?? "");
  const [nome, setNome] = useState("");
  const [categoria, setCategoria] = useState("");
  const [telefone, setTelefone] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const empresa = empresas.find((e) => e.id === empresaId);

  const categorias = useMemo(() => {
    if (!empresa) return [];
    return planoContas.filter((c) => c.segmento === empresa.segmento);
  }, [planoContas, empresa]);

  function handleEmpresaChange(id: string) {
    setEmpresaId(id);
    setCategoria("");
  }
  async function adicionar(e: React.FormEvent) {
    e.preventDefault();
    if (!empresaId || !nome.trim()) return;

    setLoading(true);
    setMessage("");

    const supabase = createClient();
    const { error } = await supabase.from("fornecedores").insert({
      empresa_id: empresaId,
      nome: nome.trim(),
      categoria_sugerida: categoria.trim() || null,
      telefone: telefone.trim() || null,
    });

    if (error) {
      setMessage(error.message);
    } else {
      setNome("");
      setCategoria("");
      setTelefone("");
      setMessage("Fornecedor cadastrado!");
      router.refresh();
    }
    setLoading(false);
  }

  async function remover(id: string) {
    if (!confirm("Remover fornecedor?")) return;
    const supabase = createClient();
    await supabase.from("fornecedores").delete().eq("id", id);
    router.refresh();
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
    <div className="grid gap-8 lg:grid-cols-2">
      <form
        onSubmit={adicionar}
        className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h2 className="mb-4 font-semibold text-slate-900">Novo fornecedor</h2>
        <div className="space-y-4">
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
              Nome do fornecedor
            </label>
            <input
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="Ex: KLEverson Scheffer"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Categoria sugerida
            </label>
            <select
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="">— Selecione —</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.nome}>
                  {c.nome}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              Telefone (opcional)
            </label>
            <input
              value={telefone}
              onChange={(e) => setTelefone(e.target.value)}
              placeholder="5599999999999"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {loading ? "Salvando…" : "Cadastrar fornecedor"}
        </button>
        {message && (
          <p className="mt-4 text-center text-sm text-slate-600">{message}</p>
        )}
      </form>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-4">
          <h2 className="font-semibold text-slate-900">
            Fornecedores cadastrados ({initial.length})
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Usados para classificar lançamentos pelo nome na descrição
          </p>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Nome</th>
              <th className="px-4 py-3 font-medium">Categoria</th>
              <th className="px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {initial.map((f) => (
              <tr key={f.id} className="border-t border-slate-100">
                <td className="px-4 py-3">{f.nome}</td>
                <td className="px-4 py-3">{f.categoria_sugerida ?? "—"}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => remover(f.id)}
                    className="text-xs text-red-600 hover:underline"
                  >
                    Remover
                  </button>
                </td>
              </tr>
            ))}
            {!initial.length && (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-slate-400">
                  Nenhum fornecedor cadastrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
