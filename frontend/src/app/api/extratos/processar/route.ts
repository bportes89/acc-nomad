import { NextResponse } from "next/server";

export async function POST(request: Request) {
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
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    return NextResponse.json(
      { error: data.detail || "Erro ao processar extrato" },
      { status: res.status },
    );
  }

  return NextResponse.json(data);
}
