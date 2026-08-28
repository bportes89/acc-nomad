export function getPublicApiUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  if (typeof window !== "undefined" && url.includes("localhost") && !window.location.hostname.includes("localhost")) {
    throw new Error(
      "NEXT_PUBLIC_API_URL não configurada na Vercel. Defina https://acc-nomad.onrender.com e redeploy.",
    );
  }
  return url;
}

async function waitForBackend(apiUrl: string, maxAttempts = 12): Promise<void> {
  for (let i = 0; i < maxAttempts; i += 1) {
    try {
      const res = await fetch(`${apiUrl}/health`, { cache: "no-store" });
      if (res.ok) return;
    } catch {
      // Render cold start — tenta de novo
    }
    await new Promise((r) => setTimeout(r, 5000));
  }
  throw new Error(
    "Backend demorou para responder (Render acordando). Tente novamente em 1 minuto.",
  );
}

export async function processarExtratoNoBackend(
  formData: FormData,
  accessToken: string,
  onStatus?: (msg: string) => void,
): Promise<Response> {
  const apiUrl = getPublicApiUrl();
  onStatus?.("Conectando ao servidor…");
  await waitForBackend(apiUrl, 12);

  onStatus?.("Processando PDF com IA (pode levar 1–2 min)…");

  return fetch(`${apiUrl}/api/extratos/processar`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: formData,
    signal: AbortSignal.timeout(180_000),
  });
}
