import { NextResponse } from "next/server";
import { runWeeklyPmgDispatch } from "@/lib/server/pmg-scheduler";

export const maxDuration = 60;

export async function POST(request: Request) {
  const { searchParams } = new URL(request.url);
  const force = searchParams.get("force") === "true";

  try {
    const result = await runWeeklyPmgDispatch({ force });
    return NextResponse.json(result);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Erro no disparo semanal";
    return NextResponse.json({ error: message }, { status: 422 });
  }
}
