-- Fix: cadastro de empresa (RLS) — migration 005 pode não ter sido aplicada em produção

drop policy if exists "empresas: authenticated insert" on public.empresas;
create policy "empresas: authenticated insert"
  on public.empresas for insert
  to authenticated
  with check (true);

drop policy if exists "empresas: member update" on public.empresas;
create policy "empresas: member update"
  on public.empresas for update
  using (public.user_belongs_to_empresa(id));

drop policy if exists "empresa_membros: self insert" on public.empresa_membros;
create policy "empresa_membros: self insert"
  on public.empresa_membros for insert
  to authenticated
  with check (user_id = auth.uid());
