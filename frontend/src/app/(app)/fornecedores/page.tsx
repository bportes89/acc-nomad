import { createClient } from "@/lib/supabase/server";
import { FornecedoresManager } from "@/components/fornecedores-manager";
import type { Empresa, Fornecedor, PlanoConta } from "@/lib/types";

export default async function FornecedoresPage() {
  const supabase = await createClient();

  const [{ data: empresas }, { data: fornecedores }, { data: planoContas }] =
    await Promise.all([
      supabase.from("empresas").select("*"),
      supabase.from("fornecedores").select("*").order("nome"),
      supabase.from("plano_contas").select("*").eq("ativo", true).order("ordem"),
    ]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Fornecedores</h1>
      <p className="mt-1 text-slate-500">
        Cadastro de fornecedores/parceiros — melhora a classificação automática
      </p>

      <div className="mt-8">
        <FornecedoresManager
          empresas={(empresas as Empresa[]) ?? []}
          fornecedores={(fornecedores as Fornecedor[]) ?? []}
          planoContas={(planoContas as PlanoConta[]) ?? []}
        />
      </div>
    </div>
  );
}
