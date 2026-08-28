-- ACC Nomad — schema inicial (greenfield)
-- Executar no SQL Editor do Supabase ou via supabase db push

-- Extensões
create extension if not exists "pgcrypto";

-- Enums
create type segmento_empresa as enum (
  'comercio',
  'servicos',
  'agro',
  'saude',
  'gastronomia',
  'supermercados',
  'eng_civil',
  'hotelaria',
  'distribuidoras'
);

create type banco_codigo as enum (
  'bb',
  'bradesco',
  'santander',
  'sicredi',
  'sicoob',
  'basa',
  'itau',
  'unicredi',
  'unknown'
);

create type extrato_status as enum (
  'pendente',
  'processando',
  'processado',
  'erro',
  'revisado'
);

create type natureza_lancamento as enum ('credito', 'debito');

create type origem_lancamento as enum ('BANCO', 'TESOURARIA');

create type revisao_acao as enum ('confirmar', 'corrigir', 'rejeitar');

-- Perfis (extensão de auth.users)
create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  nome text not null,
  email text not null unique,
  role text not null default 'revisor' check (role in ('admin', 'revisor', 'cliente')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Empresas clientes
create table public.empresas (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  cnpj text not null unique,
  segmento segmento_empresa not null default 'comercio',
  instrucao_personalizada text,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Vínculo usuário ↔ empresa
create table public.empresa_membros (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas (id) on delete cascade,
  user_id uuid not null references public.profiles (id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (empresa_id, user_id)
);

-- Plano de contas por segmento
create table public.plano_contas (
  id uuid primary key default gen_random_uuid(),
  segmento segmento_empresa not null,
  codigo text not null,
  nome text not null,
  categoria_pai text,
  ordem int not null default 0,
  ativo boolean not null default true,
  unique (segmento, codigo)
);

-- Fornecedores por empresa
create table public.fornecedores (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas (id) on delete cascade,
  nome text not null,
  categoria_sugerida text,
  telefone text,
  created_at timestamptz not null default now()
);

-- Extratos bancários
create table public.extratos (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas (id) on delete cascade,
  nome_arquivo text not null,
  banco banco_codigo,
  status extrato_status not null default 'pendente',
  total_lancamentos int not null default 0,
  erro_mensagem text,
  uploaded_by uuid references public.profiles (id),
  processed_at timestamptz,
  created_at timestamptz not null default now()
);

-- Lançamentos extraídos
create table public.lancamentos (
  id uuid primary key default gen_random_uuid(),
  extrato_id uuid not null references public.extratos (id) on delete cascade,
  empresa_id uuid not null references public.empresas (id) on delete cascade,
  data date not null,
  descricao text not null,
  valor numeric(14, 2) not null check (valor >= 0),
  natureza natureza_lancamento not null,
  categoria text,
  categoria_corrigida text,
  origem origem_lancamento not null default 'BANCO',
  revisado boolean not null default false,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

-- Tesouraria (caixa físico) — fase 2
create table public.tesouraria_lancamentos (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas (id) on delete cascade,
  data date not null,
  descricao text not null,
  valor numeric(14, 2) not null check (valor >= 0),
  natureza natureza_lancamento not null,
  categoria text,
  origem origem_lancamento not null default 'TESOURARIA',
  created_at timestamptz not null default now()
);

-- Feedback loop — revisão humana
create table public.revisoes (
  id uuid primary key default gen_random_uuid(),
  lancamento_id uuid not null references public.lancamentos (id) on delete cascade,
  revisor_id uuid not null references public.profiles (id),
  acao revisao_acao not null,
  categoria_anterior text,
  categoria_nova text,
  observacao text,
  created_at timestamptz not null default now()
);

-- Relatórios PMG gerados
create table public.relatorios_pmg (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas (id) on delete cascade,
  periodo_inicio date not null,
  periodo_fim date not null,
  dados jsonb not null default '{}',
  gerado_por uuid references public.profiles (id),
  created_at timestamptz not null default now()
);

-- Índices
create index idx_lancamentos_empresa_data on public.lancamentos (empresa_id, data);
create index idx_lancamentos_extrato on public.lancamentos (extrato_id);
create index idx_extratos_empresa on public.extratos (empresa_id, created_at desc);
create index idx_revisoes_lancamento on public.revisoes (lancamento_id);

-- Trigger updated_at
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger empresas_updated_at
  before update on public.empresas
  for each row execute function public.set_updated_at();

create trigger profiles_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

-- Auto-criar profile ao registrar usuário
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, nome, email)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'nome', split_part(new.email, '@', 1)),
    new.email
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- RLS
alter table public.profiles enable row level security;
alter table public.empresas enable row level security;
alter table public.empresa_membros enable row level security;
alter table public.plano_contas enable row level security;
alter table public.fornecedores enable row level security;
alter table public.extratos enable row level security;
alter table public.lancamentos enable row level security;
alter table public.tesouraria_lancamentos enable row level security;
alter table public.revisoes enable row level security;
alter table public.relatorios_pmg enable row level security;

-- Helper: usuário pertence à empresa
create or replace function public.user_belongs_to_empresa(p_empresa_id uuid)
returns boolean as $$
  select exists (
    select 1 from public.empresa_membros
    where empresa_id = p_empresa_id and user_id = auth.uid()
  ) or exists (
    select 1 from public.profiles
    where id = auth.uid() and role = 'admin'
  );
$$ language sql stable security definer;

-- Policies
create policy "profiles: own row"
  on public.profiles for select using (auth.uid() = id);

create policy "profiles: update own"
  on public.profiles for update using (auth.uid() = id);

create policy "empresas: member read"
  on public.empresas for select using (public.user_belongs_to_empresa(id));

create policy "empresa_membros: member read"
  on public.empresa_membros for select using (public.user_belongs_to_empresa(empresa_id));

create policy "plano_contas: authenticated read"
  on public.plano_contas for select to authenticated using (true);

create policy "fornecedores: member read"
  on public.fornecedores for select using (public.user_belongs_to_empresa(empresa_id));

create policy "extratos: member all"
  on public.extratos for all using (public.user_belongs_to_empresa(empresa_id));

create policy "lancamentos: member all"
  on public.lancamentos for all using (public.user_belongs_to_empresa(empresa_id));

create policy "tesouraria: member all"
  on public.tesouraria_lancamentos for all using (public.user_belongs_to_empresa(empresa_id));

create policy "revisoes: member read insert"
  on public.revisoes for select using (
    exists (
      select 1 from public.lancamentos l
      where l.id = lancamento_id and public.user_belongs_to_empresa(l.empresa_id)
    )
  );

create policy "revisoes: member insert"
  on public.revisoes for insert with check (
    exists (
      select 1 from public.lancamentos l
      where l.id = lancamento_id and public.user_belongs_to_empresa(l.empresa_id)
    )
  );

create policy "relatorios_pmg: member read"
  on public.relatorios_pmg for select using (public.user_belongs_to_empresa(empresa_id));

-- Seed: plano de contas varejo/comércio (base ACC)
insert into public.plano_contas (segmento, codigo, nome, categoria_pai, ordem) values
  ('comercio', 'CV01', 'Fornecedor / Revenda', 'custo_variavel', 1),
  ('comercio', 'CV02', 'Matéria-prima', 'custo_variavel', 2),
  ('comercio', 'CF01', 'Aluguel', 'custo_fixo', 1),
  ('comercio', 'CF02', 'Salários', 'custo_fixo', 2),
  ('comercio', 'CF03', 'Energia / Água / Internet', 'custo_fixo', 3),
  ('comercio', 'CF04', 'Contabilidade', 'custo_fixo', 4),
  ('comercio', 'JU01', 'Juros bancários', 'juros', 1),
  ('comercio', 'JU02', 'Multas / Tarifas', 'juros', 2),
  ('comercio', 'IN01', 'Investimentos', 'investimentos', 1),
  ('comercio', 'RC01', 'Receita de vendas', 'receita', 1),
  ('comercio', 'RC02', 'Outras receitas', 'receita', 2);

-- Storage bucket para PDFs (executar no dashboard ou via API)
-- insert into storage.buckets (id, name, public) values ('extratos', 'extratos', false);
