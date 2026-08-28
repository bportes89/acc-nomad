import nodemailer from "nodemailer";
import type { PmgResumo } from "@/lib/types";
import { getSupabaseAdmin } from "@/lib/server/supabase-admin";
import { sendWhatsAppMessage, WhatsAppError } from "@/lib/server/whatsapp";

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
      "SMTP não configurado. Defina SMTP_HOST, SMTP_USER, SMTP_PASSWORD e EMAIL_FROM (conta remetente do escritório).",
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

async function registrarEnvio(params: {
  empresa_id: string;
  periodo_inicio: string;
  periodo_fim: string;
  canal: string;
  destinatario: string;
  status: string;
  enviado_por?: string | null;
  erro_mensagem?: string | null;
  provider_name?: string | null;
  provider_message_id?: string | null;
  confirmado_em?: string | null;
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
    provider_name: params.provider_name ?? null,
    provider_message_id: params.provider_message_id ?? null,
    confirmado_em: params.confirmado_em ?? null,
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
    let providerName: string | null = null;
    let providerMessageId: string | null = null;
    let destinatarioFinal = params.destinatario;

    if (params.canal === "email") {
      await sendEmail(params.destinatario, assunto, corpo);
    } else if (params.canal === "whatsapp") {
      try {
        const wa = await sendWhatsAppMessage(params.destinatario, corpo);
        providerName = wa.provider;
        providerMessageId = wa.messageId;
        destinatarioFinal = wa.normalizedNumber;
      } catch (err) {
        const message =
          err instanceof WhatsAppError ? err.message : err instanceof Error ? err.message : String(err);
        throw new PmgDeliveryError(message);
      }
    } else {
      throw new PmgDeliveryError(`Canal inválido: ${params.canal}`);
    }

    const confirmadoEm = new Date().toISOString();

    await registrarEnvio({
      empresa_id: params.empresa_id,
      periodo_inicio: params.periodo_inicio,
      periodo_fim: params.periodo_fim,
      canal: params.canal,
      destinatario: destinatarioFinal,
      status: "enviado",
      enviado_por: params.enviado_por,
      provider_name: providerName,
      provider_message_id: providerMessageId,
      confirmado_em: confirmadoEm,
    });

    return {
      status: "enviado",
      canal: params.canal,
      destinatario: destinatarioFinal,
      provider_name: providerName,
      provider_message_id: providerMessageId,
    };
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
