"use client";

import { useState } from "react";
import { AlertCircle, X } from "lucide-react";
import { ReportErroForm, buildExtratoReportPrefill } from "@/components/report-erro-form";
import type { Empresa, Extrato } from "@/lib/types";

export function ReportErroDialog({
  extrato,
  empresas,
}: {
  extrato: Extrato;
  empresas: Empresa[];
}) {
  const [open, setOpen] = useState(false);

  if (extrato.status !== "erro") return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        title="Reportar erro"
        className="rounded p-1 text-amber-600 hover:bg-amber-50"
      >
        <AlertCircle size={16} />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-slate-600"
            >
              <X size={20} />
            </button>
            <h3 className="mb-4 pr-8 text-lg font-semibold text-slate-900">
              Reportar erro do extrato
            </h3>
            <ReportErroForm
              empresas={empresas}
              prefill={buildExtratoReportPrefill(extrato)}
              compact
              onSuccess={() => setOpen(false)}
            />
          </div>
        </div>
      )}
    </>
  );
}
