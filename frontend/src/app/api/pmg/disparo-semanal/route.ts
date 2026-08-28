import { NextResponse } from "next/server";
import { formatUserError } from "@/lib/format-api-error";
import { runWeeklyPmgDispatch } from "@/lib/server/pmg-scheduler";

export const maxDuration = 60;

export async function POST(request: Request) {
  const { searchParams } = new URL(request.url);
  const force = searchParams.get("force") === "true";
  const periodo = searchParams.get("periodo") ?? undefined;

  try {
    const result = await runWeeklyPmgDispatch({ force, periodo });
    return NextResponse.json(result);
  } catch (err) {
    const message = formatUserError(
      err instanceof Error ? err.message : "",
      "Erro no disparo semanal.",
    );
    return NextResponse.json({ error: message }, { status: 422 });
  }
}
