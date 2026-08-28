export function formatSupabaseError(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes("criar_empresa_onboarding") || lower.includes("could not find the function")) {
    return "Cadastro de empresa não configurado no banco. Avise o suporte para aplicar a migration 011 no Supabase.";
  }
  if (lower.includes("row-level security") && lower.includes("empresas")) {
    return "Não foi possível cadastrar a empresa: falta permissão no banco de dados (RLS). Avise o suporte para aplicar a migration 011 no Supabase.";
  }
  if (lower.includes("row-level security") && lower.includes("empresa_membros")) {
    return "Empresa criada, mas não foi possível vincular à sua conta. Avise o suporte (RLS empresa_membros).";
  }
  if (lower.includes("row-level security")) {
    return "Operação bloqueada pela política de segurança do banco. Avise o suporte.";
  }
  if (lower.includes("duplicate key") && lower.includes("cnpj")) {
    return "Este CNPJ já está cadastrado.";
  }
  return message;
}

export function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
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
    if (typeof err === "string" && err.trim()) return err;
  }
  return fallback;
}
