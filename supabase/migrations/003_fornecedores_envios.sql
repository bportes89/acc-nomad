-- Fornecedores: permitir CRUD para membros da empresa
-- Envios PMG: histórico de entregas WhatsApp/Email

create policy "fornecedores: member insert"
  on public.fornecedores for insert
  with check (public.user_belongs_to_empresa(empresa_id));

create policy "fornecedores: member update"
  on public.fornecedores for update
  using (public.user_belongs_to_empresa(empresa_id));

create policy "fornecedores: member delete"
  on public.fornecedores for delete
  using (public.user_belongs_to_empresa(empresa_id));

create type canal_envio as enum ('email', 'whatsapp');

create type status_envio as enum ('enviado', 'erro', 'pendente');

create table public.envios_pmg (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas (id) on delete cascade,
  periodo_inicio date not null,
  periodo_fim date not null,
  canal canal_envio not null,
  destinatario text not null,
  status status_envio not null default 'pendente',
  erro_mensagem text,
  enviado_por uuid references public.profiles (id),
  created_at timestamptz not null default now()
);

create index idx_envios_pmg_empresa on public.envios_pmg (empresa_id, created_at desc);

alter table public.envios_pmg enable row level security;

create policy "envios_pmg: member read"
  on public.envios_pmg for select
  using (public.user_belongs_to_empresa(empresa_id));

create policy "envios_pmg: member insert"
  on public.envios_pmg for insert
  with check (public.user_belongs_to_empresa(empresa_id));
