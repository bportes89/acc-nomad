import { NextResponse } from "next/server";
import { formatUserError } from "@/lib/format-api-error";
import { enviarPmg, PmgDeliveryError } from "@/lib/server/pmg-delivery";
import type { PmgResumo } from "@/lib/types";

export const maxDuration = 60;

function periodoBounds(periodo: string) {
  const [year, month] = periodo.split("-").map(Number);
  const periodo_inicio = `${periodo}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const periodo_fim = `${periodo}-${String(lastDay).padStart(2, "0")}`;
  return { periodo_inicio, periodo_fim };
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { periodo_inicio, periodo_fim } = periodoBounds(String(body.periodo));

    const result = await enviarPmg({
      empresa_id: body.empresa_id,
      empresa_nome: body.empresa_nome,
      periodo: body.periodo,
      periodo_inicio,
      periodo_fim,
      canal: body.canal,
      destinatario: body.destinatario,
      resumo: body.resumo as PmgResumo,
      enviado_por: body.enviado_por ?? null,
    });

    return NextResponse.json(result);
  } catch (err) {
    const raw =
      err instanceof PmgDeliveryError
        ? err.message
        : err instanceof Error
          ? err.message
          : "";
    const message = formatUserError(raw, "Erro ao enviar PMG.");

    return NextResponse.json({ error: message }, { status: 422 });
  }
}
