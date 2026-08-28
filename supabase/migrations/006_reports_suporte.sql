-- Report de erro (Ticketed Support)

create type report_erro_categoria as enum (
  'extrato',
  'classificacao',
  'pmg',
  'login',
  'outro'
);

create type report_erro_status as enum (
  'aberto',
  'em_analise',
  'resolvido'
);

create table public.reports_erro (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  empresa_id uuid references public.empresas (id) on delete set null,
  extrato_id uuid references public.extratos (id) on delete set null,
  categoria report_erro_categoria not null default 'outro',
  titulo text not null,
  descricao text not null,
  status report_erro_status not null default 'aberto',
  resposta text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_reports_erro_user on public.reports_erro (user_id, created_at desc);
create index idx_reports_erro_status on public.reports_erro (status, created_at desc);

alter table public.reports_erro enable row level security;

create policy "reports_erro: own read"
  on public.reports_erro for select
  using (auth.uid() = user_id);

create policy "reports_erro: own insert"
  on public.reports_erro for insert
  with check (auth.uid() = user_id);

create policy "reports_erro: admin read all"
  on public.reports_erro for select
  using (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and role = 'admin'
    )
  );

create policy "reports_erro: admin update"
  on public.reports_erro for update
  using (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and role = 'admin'
    )
  );
