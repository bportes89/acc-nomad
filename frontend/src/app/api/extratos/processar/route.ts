import { NextResponse } from "next/server";
import { formatApiError } from "@/lib/format-api-error";

export const maxDuration = 60;

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const apiUrl =
      process.env.API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000";
    const apiSecret = process.env.API_SECRET || "";

    const res = await fetch(`${apiUrl}/api/extratos/processar`, {
      method: "POST",
      headers: { "X-Api-Secret": apiSecret },
      body: formData,
      signal: AbortSignal.timeout(55_000),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      return NextResponse.json(
        {
          error: formatApiError(
            data.detail ?? data.error,
            res.status === 504 || res.status === 408
              ? "Timeout — o PDF pode ser grande. Tente pelo navegador direto ao backend."
              : "Erro ao processar extrato",
          ),
        },
        { status: res.status },
      );
    }

    return NextResponse.json(data);
  } catch (err) {
    const msg =
      err instanceof Error && err.name === "TimeoutError"
        ? "Timeout ao processar (limite Vercel). Recarregue a página e tente de novo — o upload agora vai direto ao Render."
        : err instanceof Error
          ? err.message
          : "Falha de conexão com o backend";
    return NextResponse.json({ error: msg }, { status: 502 });
  }
}
