export type WhatsAppProvider = "generic" | "evolution" | "zapi";

/** WhatsApp PMG só envia quando WHATSAPP_API_URL estiver na Vercel/backend. */
export function isWhatsAppConfigured(): boolean {
  return Boolean(process.env.WHATSAPP_API_URL?.trim());
}

export class WhatsAppError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WhatsAppError";
  }
}

export interface WhatsAppSendResult {
  provider: WhatsAppProvider;
  messageId: string | null;
  normalizedNumber: string;
}

export function normalizeWhatsAppNumber(input: string): string {
  let digits = input.replace(/\D/g, "");
  if (digits.startsWith("0")) {
    digits = digits.slice(1);
  }
  if (!digits.startsWith("55") && (digits.length === 10 || digits.length === 11)) {
    digits = `55${digits}`;
  }
  if (digits.length < 12 || digits.length > 15) {
    throw new WhatsAppError(
      "Número WhatsApp inválido. Use DDI+DDD+número, ex: 5511999999999 ou (11) 99999-9999.",
    );
  }
  return digits;
}

function providerFromEnv(): WhatsAppProvider {
  const raw = (process.env.WHATSAPP_PROVIDER || "generic").toLowerCase();
  if (raw === "evolution" || raw === "zapi" || raw === "generic") {
    return raw;
  }
  return "generic";
}

function extractMessageId(provider: WhatsAppProvider, data: unknown): string | null {
  if (!data || typeof data !== "object") return null;
  const obj = data as Record<string, unknown>;

  const candidates = [
    obj.messageId,
    obj.message_id,
    obj.id,
    obj.zaapId,
    obj.zaap_id,
  ];

  const key = obj.key;
  if (key && typeof key === "object") {
    const keyObj = key as Record<string, unknown>;
    candidates.push(keyObj.id);
  }

  for (const value of candidates) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  void provider;
  return null;
}

function buildRequest(
  provider: WhatsAppProvider,
  number: string,
  message: string,
): { url: string; headers: Record<string, string>; body: object } {
  const url = process.env.WHATSAPP_API_URL;
  if (!url) {
    throw new WhatsAppError(
      "WhatsApp não configurado. Defina WHATSAPP_API_URL na Vercel (Settings → Environment Variables).",
    );
  }

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = process.env.WHATSAPP_API_TOKEN;
  if (token) {
    if (provider === "zapi") {
      headers["Client-Token"] = token;
    } else {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  if (provider === "evolution") {
    const evoHeaders: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) {
      evoHeaders.apikey = token;
    }
    return {
      url,
      headers: evoHeaders,
      body: { number, text: message },
    };
  }

  if (provider === "zapi") {
    return {
      url,
      headers,
      body: { phone: number, message },
    };
  }

  return {
    url,
    headers,
    body: { number, message },
  };
}

export async function sendWhatsAppMessage(
  destinatario: string,
  mensagem: string,
): Promise<WhatsAppSendResult> {
  const provider = providerFromEnv();
  const normalizedNumber = normalizeWhatsAppNumber(destinatario);
  const { url, headers, body } = buildRequest(provider, normalizedNumber, mensagem);

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text.slice(0, 500) };
  }

  if (!res.ok) {
    const detail =
      data && typeof data === "object" && "message" in data
        ? String((data as { message: unknown }).message)
        : text.slice(0, 200);
    throw new WhatsAppError(`WhatsApp API erro ${res.status}: ${detail}`);
  }

  return {
    provider,
    messageId: extractMessageId(provider, data),
    normalizedNumber,
  };
}
