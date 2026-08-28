import { createClient } from "@/lib/supabase/server";
import { ReportErroForm, ReportsList } from "@/components/report-erro-form";
import type { Empresa, ReportErro } from "@/lib/types";

export default async function SuportePage() {
  const supabase = await createClient();

  const [{ data: empresas }, { data: reports }] = await Promise.all([
    supabase.from("empresas").select("*").order("nome"),
    supabase
      .from("reports_erro")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(50),
  ]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Suporte</h1>
      <p className="mt-1 text-slate-500">
        Report de erro (Ticketed Support) — descreva problemas para nossa equipe analisar
      </p>

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <ReportErroForm empresas={(empresas as Empresa[]) ?? []} />
        <ReportsList reports={(reports as ReportErro[]) ?? []} />
      </div>
    </div>
  );
}
