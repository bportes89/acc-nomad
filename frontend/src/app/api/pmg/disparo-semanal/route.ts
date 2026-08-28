import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const { searchParams } = new URL(request.url);
  const force = searchParams.get("force") === "true";

  const apiUrl =
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";
  const apiSecret = process.env.API_SECRET || "";

  const res = await fetch(
    `${apiUrl}/api/pmg/disparo-semanal?force=${force}`,
    {
      method: "POST",
      headers: {
        "X-Api-Secret": apiSecret,
      },
    },
  );

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    return NextResponse.json(
      { error: data.detail || "Erro no disparo semanal" },
      { status: res.status },
    );
  }

  return NextResponse.json(data);
}
