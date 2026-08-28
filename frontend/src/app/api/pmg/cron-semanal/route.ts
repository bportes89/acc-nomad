import { NextResponse } from "next/server";
import { runWeeklyPmgDispatch } from "@/lib/server/pmg-scheduler";

export const maxDuration = 60;

export async function GET(request: Request) {
  const authHeader = request.headers.get("authorization");
  const cronSecret = process.env.CRON_SECRET;

  if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const result = await runWeeklyPmgDispatch({ force: false });
    return NextResponse.json(result);
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Erro no disparo semanal";
    return NextResponse.json({ error: message }, { status: 422 });
  }
}
