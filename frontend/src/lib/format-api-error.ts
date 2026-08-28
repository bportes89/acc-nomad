/** Traduz mensagens de erro (Supabase, Postgres, Auth, API) para português do Brasil. */

const EXACT: Record<string, string> = {
  "Invalid login credentials": "E-mail ou senha incorretos.",
  "Email not confirmed": "Confirme seu e-mail antes de entrar.",
  "User already registered": "Este e-mail já está cadastrado.",
  "Signups not allowed for this instance": "Cadastro de novas contas está desabilitado.",
  "Password should be at least 6 characters":
    "A senha deve ter pelo menos 6 caracteres.",
  "Unable to validate email address: invalid format": "Informe um e-mail válido.",
  "For security purposes, you can only request this once every 60 seconds":
    "Aguarde 1 minuto antes de solicitar outro e-mail.",
  "Email rate limit exceeded":
    "Limite de envio de e-mails atingido. Tente novamente em alguns minutos.",
  "Auth session missing!": "Sessão expirada. Faça login novamente.",
  "JWT expired": "Sessão expirada. Faça login novamente.",
  "Invalid Refresh Token: Refresh Token Not Found":
    "Sessão expirada. Faça login novamente.",
  "User not found": "Usuário não encontrado.",
  "New password should be different from the old password.":
    "A nova senha deve ser diferente da senha atual.",
  "Same password": "A nova senha deve ser diferente da senha atual.",
  "Failed to fetch": "Falha de conexão. Verifique sua internet e tente novamente.",
  "NetworkError when attempting to fetch resource.":
    "Falha de conexão. Verifique sua internet e tente novamente.",
};

type PatternRule = { match: (text: string) => boolean; message: string };

const PATTERNS: PatternRule[] = [
  {
    match: (t) =>
      t.includes("criar_empresa_onboarding") ||
      t.toLowerCase().includes("could not find the function"),
    message:
      "Cadastro de empresa não configurado no banco. Avise o suporte para aplicar a migration 011 no Supabase.",
  },
  {
    match: (t) =>
      t.toLowerCase().includes("row-level security") &&
      t.toLowerCase().includes("empresas"),
    message:
      "Não foi possível cadastrar a empresa por falta de permissão no banco. Avise o suporte.",
  },
  {
    match: (t) =>
      t.toLowerCase().includes("row-level security") &&
      t.toLowerCase().includes("empresa_membros"),
    message:
      "Empresa criada, mas não foi possível vincular à sua conta. Avise o suporte.",
  },
  {
    match: (t) => t.toLowerCase().includes("row-level security"),
    message:
      "Operação bloqueada pela política de segurança do banco. Avise o suporte.",
  },
  {
    match: (t) =>
      t.toLowerCase().includes("duplicate key") &&
      (t.toLowerCase().includes("cnpj") || t.toLowerCase().includes("empresas")),
    message: "Este CNPJ já está cadastrado.",
  },
  {
    match: (t) => t.toLowerCase().includes("duplicate key"),
    message: "Registro duplicado. Verifique se os dados já existem.",
  },
  {
    match: (t) => t.toLowerCase().includes("violates foreign key constraint"),
    message: "Não foi possível salvar: referência inválida (empresa ou registro inexistente).",
  },
  {
    match: (t) => t.toLowerCase().includes("null value in column"),
    message: "Preencha todos os campos obrigatórios.",
  },
  {
    match: (t) => t.toLowerCase().includes("permission denied"),
    message: "Sem permissão para esta operação. Faça login novamente ou avise o suporte.",
  },
  {
    match: (t) => t.toLowerCase().includes("not authorized"),
    message: "Não autorizado. Faça login novamente.",
  },
  {
    match: (t) => t.toLowerCase().includes("timeout"),
    message: "A operação demorou demais. Tente novamente.",
  },
  {
    match: (t) => t.toLowerCase().includes("api secret"),
    message: "Erro de autenticação com o servidor. Avise o suporte.",
  },
  {
    match: (t) =>
      t.toLowerCase().includes("configure") &&
      t.toLowerCase().includes("supabase_service_role_key"),
    message:
      "Envio automático não configurado no servidor. Avise o suporte (SUPABASE_SERVICE_ROLE_KEY).",
  },
  {
    match: (t) => t.toLowerCase().includes("smtp") && t.toLowerCase().includes("configurado"),
    message: "Envio por e-mail não configurado. Avise o suporte.",
  },
  {
    match: (t) => t.toLowerCase().includes("whatsapp") && t.toLowerCase().includes("configurado"),
    message: "WhatsApp ainda não configurado. Use e-mail ou avise o suporte.",
  },
];

function exactMatch(message: string): string | null {
  const direct = EXACT[message];
  if (direct) return direct;

  const lower = message.toLowerCase();
  for (const [key, value] of Object.entries(EXACT)) {
    if (key.toLowerCase() === lower) return value;
  }
  return null;
}

/** Traduz qualquer mensagem de erro exibida ao usuário. */
export function formatUserError(message: string, fallback?: string): string {
  const trimmed = message.trim();
  if (!trimmed) {
    return fallback ?? "Ocorreu um erro inesperado. Tente novamente.";
  }

  const exact = exactMatch(trimmed);
  if (exact) return exact;

  for (const rule of PATTERNS) {
    if (rule.match(trimmed)) return rule.message;
  }

  // Mensagens já em português (com ou sem acento)
  if (/[áàâãéêíóôõúç]/i.test(trimmed)) {
    return trimmed;
  }
  if (
    /^(erro|não|nao|pdf|sessão|sessao|informe|aguarde|operação|operacao|cadastro|envio|timeout|backend|whatsapp|smtp|extrato|empresa|fornecedor|pmg|conta|senha|e-mail|email)/i.test(
      trimmed,
    )
  ) {
    return trimmed;
  }

  // Erro técnico em inglês sem tradução específica
  if (/^[a-z0-9\s.,'":\-_()/!]+$/i.test(trimmed) && !/[áàâãéêíóôõúç]/i.test(trimmed)) {
    return (
      fallback ??
      "Não foi possível concluir a operação. Tente novamente ou avise o suporte."
    );
  }

  return trimmed;
}

/** @deprecated Use formatUserError */
export const formatSupabaseError = formatUserError;

function extractRawMessage(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim()) {
    return detail.trim();
  }
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: string }).msg);
        }
        return null;
      })
      .filter(Boolean);
    if (msgs.length) return msgs.join("; ");
  }
  if (detail && typeof detail === "object" && "error" in detail) {
    const err = (detail as { error: unknown }).error;
    if (typeof err === "string" && err.trim()) return err.trim();
  }
  return null;
}

export function formatApiError(detail: unknown, fallback: string): string {
  const raw = extractRawMessage(detail);
  if (raw) return formatUserError(raw, fallback);
  return fallback;
}
