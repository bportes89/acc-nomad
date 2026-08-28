import { createClient } from "@/lib/supabase/server";
import { EmpresaOnboarding } from "@/components/empresa-onboarding";
import type { Empresa, PlanoConta } from "@/lib/types";

export default async function EmpresasPage() {
  const supabase = await createClient();

  const [{ data: empresas }, { data: planoContas }] = await Promise.all([
    supabase.from("empresas").select("*").order("nome"),
    supabase.from("plano_contas").select("*").eq("ativo", true).order("ordem"),
  ]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Empresas</h1>
      <p className="mt-1 text-slate-500">
        Onboarding: cadastre a empresa, escolha o segmento e configure o plano de contas ACC
      </p>

      <div className="mt-8">
        <EmpresaOnboarding
          empresas={(empresas as Empresa[]) ?? []}
          planoContas={(planoContas as PlanoConta[]) ?? []}
        />
      </div>
    </div>
  );
}
