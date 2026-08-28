export function getPublicApiUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  if (
    typeof window !== "undefined" &&
    url.includes("localhost") &&
    !window.location.hostname.includes("localhost")
  ) {
    throw new Error(
      "NEXT_PUBLIC_API_URL não configurada na Vercel. Defina https://acc-nomad.onrender.com e redeploy.",
    );
  }
  return url.replace(/\/$/, "");
}

export async function processarExtratoNoBackend(
  formData: FormData,
  accessToken: string,
  onStatus?: (msg: string) => void,
): Promise<Response> {
  const apiUrl = getPublicApiUrl();

  onStatus?.(
    "Extraindo lançamentos e classificando… Geralmente leva menos de 1 minuto.",
  );

  try {
    return await fetch(`${apiUrl}/api/extratos/processar`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      body: formData,
      signal: AbortSignal.timeout(120_000),
    });
  } catch (err) {
    const isTimeout =
      err instanceof DOMException && err.name === "TimeoutError";
    if (isTimeout) {
      throw new Error(
        "O processamento passou de 2 minutos. Tente novamente — se persistir, avise o suporte.",
      );
    }
    throw new Error(
      `Backend indisponível (${apiUrl}). Abra ${apiUrl}/health no navegador — se não responder, reinicie o serviço no painel Render.`,
    );
  }
}
