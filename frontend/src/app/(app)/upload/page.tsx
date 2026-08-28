import { createClient } from "@/lib/supabase/server";
import { UploadForm } from "@/components/upload-form";
import type { Empresa } from "@/lib/types";

export default async function UploadPage() {
  const supabase = await createClient();
  const { data: empresas } = await supabase.from("empresas").select("*");

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Upload de extratos</h1>
      <p className="mt-1 text-slate-500">
        Envie PDFs de extrato bancário para processamento automático
      </p>

      <div className="mt-8 max-w-xl">
        <UploadForm empresas={(empresas as Empresa[]) ?? []} />
      </div>
    </div>
  );
}
