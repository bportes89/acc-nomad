import nodemailer from "nodemailer";
import type { PmgResumo } from "@/lib/types";
import { getSupabaseAdmin } from "@/lib/server/supabase-admin";

export class PmgDeliveryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PmgDeliveryError";
  }
}

function formatPmgText(resumo: PmgResumo, periodo: string, empresa: string): string {
  const resultado =
    resumo.receita -
    resumo.custo_variavel -
    resumo.custo_fixo -
    resumo.juros -
    resumo.investimentos;

  return `ACC Nomad — Relatório PMG
Empresa: ${empresa}
Período: ${periodo}

Receita:          R$ ${resumo.receita.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
Custo Variável:   R$ ${resumo.custo_variavel.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
Custo Fixo:       R$ ${resumo.custo_fixo.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
Juros:            R$ ${resumo.juros.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
Investimentos:    R$ ${resumo.investimentos.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
─────────────────────────
Resultado:        R$ ${resultado.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}

Gerado automaticamente pelo ACC Nomad.
`;
}

async function sendEmail(destinatario: string, assunto: string, corpo: string): Promise<void> {
  const host = process.env.SMTP_HOST;
  const from = process.env.EMAIL_FROM;

  if (!host || !from) {
    throw new PmgDeliveryError(
      "SMTP não configurado na Vercel. Defina SMTP_HOST, SMTP_USER, SMTP_PASSWORD e EMAIL_FROM.",
    );
  }

  const port = Number(process.env.SMTP_PORT || 587);
  const transporter = nodemailer.createTransport({
    host,
    port,
    secure: port === 465,
    auth: process.env.SMTP_USER
      ? {
          user: process.env.SMTP_USER,
          pass: process.env.SMTP_PASSWORD || "",
        }
      : undefined,
  });

  await transporter.sendMail({
    from,
    to: destinatario,
    subject: assunto,
    text: corpo,
  });
}

async function sendWhatsApp(destinatario: string, mensagem: string): Promise<void> {
  const url = process.env.WHATSAPP_API_URL;
  if (!url) {
    throw new PmgDeliveryError(
      "WhatsApp não configurado. Defina WHATSAPP_API_URL e WHATSAPP_API_TOKEN na Vercel.",
    );
  }

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (process.env.WHATSAPP_API_TOKEN) {
    headers.Authorization = `Bearer ${process.env.WHATSAPP_API_TOKEN}`;
  }

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ number: destinatario, message: mensagem }),
  });

  if (!res.ok) {
    const text = (await res.text()).slice(0, 200);
    throw new PmgDeliveryError(`WhatsApp API erro ${res.status}: ${text}`);
  }
}

async function registrarEnvio(params: {
  empresa_id: string;
  periodo_inicio: string;
  periodo_fim: string;
  canal: string;
  destinatario: string;
  status: string;
  enviado_por?: string | null;
  erro_mensagem?: string | null;
}) {
  const supabase = getSupabaseAdmin();
  await supabase.from("envios_pmg").insert({
    empresa_id: params.empresa_id,
    periodo_inicio: params.periodo_inicio,
    periodo_fim: params.periodo_fim,
    canal: params.canal,
    destinatario: params.destinatario,
    status: params.status,
    enviado_por: params.enviado_por ?? null,
    erro_mensagem: params.erro_mensagem ?? null,
  });
}

export async function enviarPmg(params: {
  empresa_id: string;
  empresa_nome: string;
  periodo: string;
  periodo_inicio: string;
  periodo_fim: string;
  canal: "email" | "whatsapp";
  destinatario: string;
  resumo: PmgResumo;
  enviado_por?: string | null;
}) {
  const corpo = formatPmgText(params.resumo, params.periodo, params.empresa_nome);
  const assunto = `ACC Nomad — PMG ${params.periodo} — ${params.empresa_nome}`;

  try {
    if (params.canal === "email") {
      await sendEmail(params.destinatario, assunto, corpo);
    } else if (params.canal === "whatsapp") {
      await sendWhatsApp(params.destinatario, corpo);
    } else {
      throw new PmgDeliveryError(`Canal inválido: ${params.canal}`);
    }

    await registrarEnvio({
      empresa_id: params.empresa_id,
      periodo_inicio: params.periodo_inicio,
      periodo_fim: params.periodo_fim,
      canal: params.canal,
      destinatario: params.destinatario,
      status: "enviado",
      enviado_por: params.enviado_por,
    });

    return { status: "enviado", canal: params.canal, destinatario: params.destinatario };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    await registrarEnvio({
      empresa_id: params.empresa_id,
      periodo_inicio: params.periodo_inicio,
      periodo_fim: params.periodo_fim,
      canal: params.canal,
      destinatario: params.destinatario,
      status: "erro",
      enviado_por: params.enviado_por,
      erro_mensagem: message,
    });
    throw new PmgDeliveryError(message);
  }
}
