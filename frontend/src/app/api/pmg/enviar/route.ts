import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();
  const apiUrl =
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000";
  const apiSecret = process.env.API_SECRET || "";

  const res = await fetch(`${apiUrl}/api/pmg/enviar`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Secret": apiSecret,
    },
    body: JSON.stringify(body),
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    return NextResponse.json(
      { error: data.detail || "Erro ao enviar PMG" },
      { status: res.status },
    );
  }

  return NextResponse.json(data);
}
