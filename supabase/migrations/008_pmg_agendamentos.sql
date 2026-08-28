-- Agendamento de envio semanal automático do PMG
-- Tipos usados também em 003; criar aqui se 003 não foi aplicada.

do $$ begin
  create type public.canal_envio as enum ('email', 'whatsapp');
exception
  when duplicate_object then null;
end $$;

create table if not exists public.pmg_agendamentos (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas (id) on delete cascade,
  canal canal_envio not null default 'email',
  destinatario text not null,
  dia_semana int not null default 0 check (dia_semana between 0 and 6),
  ativo boolean not null default true,
  ultimo_envio_em timestamptz,
  created_by uuid references public.profiles (id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (empresa_id, destinatario, canal)
);

comment on column public.pmg_agendamentos.dia_semana is
  '0=segunda, 1=terça, ..., 6=domingo (padrão Python weekday)';

create index if not exists idx_pmg_agendamentos_ativo on public.pmg_agendamentos (ativo, dia_semana);

drop trigger if exists pmg_agendamentos_updated_at on public.pmg_agendamentos;
create trigger pmg_agendamentos_updated_at
  before update on public.pmg_agendamentos
  for each row execute function public.set_updated_at();

alter table public.pmg_agendamentos enable row level security;

drop policy if exists "pmg_agendamentos: member read" on public.pmg_agendamentos;
create policy "pmg_agendamentos: member read"
  on public.pmg_agendamentos for select
  using (public.user_belongs_to_empresa(empresa_id));

drop policy if exists "pmg_agendamentos: member insert" on public.pmg_agendamentos;
create policy "pmg_agendamentos: member insert"
  on public.pmg_agendamentos for insert
  with check (public.user_belongs_to_empresa(empresa_id));

drop policy if exists "pmg_agendamentos: member update" on public.pmg_agendamentos;
create policy "pmg_agendamentos: member update"
  on public.pmg_agendamentos for update
  using (public.user_belongs_to_empresa(empresa_id));

drop policy if exists "pmg_agendamentos: member delete" on public.pmg_agendamentos;
create policy "pmg_agendamentos: member delete"
  on public.pmg_agendamentos for delete
  using (public.user_belongs_to_empresa(empresa_id));
