-- Onboarding: criar empresa + vínculo em uma transação (contorna RLS no INSERT…RETURNING)

create or replace function public.criar_empresa_onboarding(
  p_nome text,
  p_cnpj text,
  p_segmento segmento_empresa,
  p_instrucao text default null
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_empresa_id uuid;
  v_user_id uuid;
begin
  v_user_id := auth.uid();
  if v_user_id is null then
    raise exception 'Faça login novamente para cadastrar a empresa.';
  end if;

  if p_nome is null or trim(p_nome) = '' then
    raise exception 'Informe o nome da empresa.';
  end if;

  if p_cnpj is null or length(regexp_replace(p_cnpj, '\D', '', 'g')) <> 14 then
    raise exception 'Informe um CNPJ válido (14 dígitos).';
  end if;

  insert into public.empresas (nome, cnpj, segmento, instrucao_personalizada)
  values (
    trim(p_nome),
    regexp_replace(p_cnpj, '\D', '', 'g'),
    p_segmento,
    nullif(trim(coalesce(p_instrucao, '')), '')
  )
  returning id into v_empresa_id;

  insert into public.empresa_membros (empresa_id, user_id)
  values (v_empresa_id, v_user_id);

  return v_empresa_id;
end;
$$;

revoke all on function public.criar_empresa_onboarding(text, text, segmento_empresa, text) from public;
grant execute on function public.criar_empresa_onboarding(text, text, segmento_empresa, text) to authenticated;
