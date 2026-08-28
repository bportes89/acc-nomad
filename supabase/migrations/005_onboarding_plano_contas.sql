-- Onboarding: CRUD de empresas + plano de contas por segmento

-- Empresas: criar e editar (membros ou admin)
create policy "empresas: authenticated insert"
  on public.empresas for insert
  to authenticated
  with check (true);

create policy "empresas: member update"
  on public.empresas for update
  using (public.user_belongs_to_empresa(id));

-- Vínculo usuário ↔ empresa (auto-onboarding)
create policy "empresa_membros: self insert"
  on public.empresa_membros for insert
  to authenticated
  with check (user_id = auth.uid());

-- Plano de contas por segmento (comércio já existe em 001)
insert into public.plano_contas (segmento, codigo, nome, categoria_pai, ordem) values
  -- Serviços
  ('servicos', 'CV01', 'Fornecedor / Subcontratado', 'custo_variavel', 1),
  ('servicos', 'CV02', 'Materiais de consumo', 'custo_variavel', 2),
  ('servicos', 'CF01', 'Aluguel', 'custo_fixo', 1),
  ('servicos', 'CF02', 'Salários / Pró-labore', 'custo_fixo', 2),
  ('servicos', 'CF03', 'Energia / Internet', 'custo_fixo', 3),
  ('servicos', 'CF04', 'Contabilidade', 'custo_fixo', 4),
  ('servicos', 'JU01', 'Juros bancários', 'juros', 1),
  ('servicos', 'JU02', 'Multas / Tarifas', 'juros', 2),
  ('servicos', 'IN01', 'Investimentos', 'investimentos', 1),
  ('servicos', 'RC01', 'Receita de serviços', 'receita', 1),
  ('servicos', 'RC02', 'Outras receitas', 'receita', 2),
  -- Agro
  ('agro', 'CV01', 'Insumos / Sementes', 'custo_variavel', 1),
  ('agro', 'CV02', 'Fertilizantes / Defensivos', 'custo_variavel', 2),
  ('agro', 'CF01', 'Aluguel / Arrendamento', 'custo_fixo', 1),
  ('agro', 'CF02', 'Salários / Mão de obra', 'custo_fixo', 2),
  ('agro', 'CF03', 'Combustível / Manutenção', 'custo_fixo', 3),
  ('agro', 'CF04', 'Contabilidade', 'custo_fixo', 4),
  ('agro', 'JU01', 'Juros bancários', 'juros', 1),
  ('agro', 'JU02', 'Multas / Tarifas', 'juros', 2),
  ('agro', 'IN01', 'Investimentos / Maquinário', 'investimentos', 1),
  ('agro', 'RC01', 'Receita agrícola', 'receita', 1),
  ('agro', 'RC02', 'Outras receitas', 'receita', 2),
  -- Saúde
  ('saude', 'CV01', 'Materiais médicos', 'custo_variavel', 1),
  ('saude', 'CV02', 'Medicamentos / Insumos', 'custo_variavel', 2),
  ('saude', 'CF01', 'Aluguel', 'custo_fixo', 1),
  ('saude', 'CF02', 'Salários / Honorários', 'custo_fixo', 2),
  ('saude', 'CF03', 'Energia / Internet', 'custo_fixo', 3),
  ('saude', 'CF04', 'Contabilidade', 'custo_fixo', 4),
  ('saude', 'JU01', 'Juros bancários', 'juros', 1),
  ('saude', 'JU02', 'Multas / Tarifas', 'juros', 2),
  ('saude', 'IN01', 'Investimentos / Equipamentos', 'investimentos', 1),
  ('saude', 'RC01', 'Receita de consultas', 'receita', 1),
  ('saude', 'RC02', 'Outras receitas', 'receita', 2),
  -- Gastronomia
  ('gastronomia', 'CV01', 'Insumos / CMV', 'custo_variavel', 1),
  ('gastronomia', 'CV02', 'Bebidas / Revenda', 'custo_variavel', 2),
  ('gastronomia', 'CF01', 'Aluguel', 'custo_fixo', 1),
  ('gastronomia', 'CF02', 'Salários / Encargos', 'custo_fixo', 2),
  ('gastronomia', 'CF03', 'Gás / Energia', 'custo_fixo', 3),
  ('gastronomia', 'CF04', 'Contabilidade', 'custo_fixo', 4),
  ('gastronomia', 'JU01', 'Juros bancários', 'juros', 1),
  ('gastronomia', 'JU02', 'Multas / Tarifas', 'juros', 2),
  ('gastronomia', 'IN01', 'Investimentos', 'investimentos', 1),
  ('gastronomia', 'RC01', 'Receita de vendas', 'receita', 1),
  ('gastronomia', 'RC02', 'Outras receitas', 'receita', 2),
  -- Supermercados
  ('supermercados', 'CV01', 'Fornecedor / Revenda', 'custo_variavel', 1),
  ('supermercados', 'CV02', 'Perdas / Quebras', 'custo_variavel', 2),
  ('supermercados', 'CF01', 'Aluguel', 'custo_fixo', 1),
  ('supermercados', 'CF02', 'Salários', 'custo_fixo', 2),
  ('supermercados', 'CF03', 'Energia / Refrigeracao', 'custo_fixo', 3),
  ('supermercados', 'CF04', 'Contabilidade', 'custo_fixo', 4),
  ('supermercados', 'JU01', 'Juros bancários', 'juros', 1),
  ('supermercados', 'JU02', 'Multas / Tarifas', 'juros', 2),
  ('supermercados', 'IN01', 'Investimentos', 'investimentos', 1),
  ('supermercados', 'RC01', 'Receita de vendas', 'receita', 1),
  ('supermercados', 'RC02', 'Outras receitas', 'receita', 2),
  -- Engenharia civil
  ('eng_civil', 'CV01', 'Materiais de obra', 'custo_variavel', 1),
  ('eng_civil', 'CV02', 'Subempreiteiros', 'custo_variavel', 2),
  ('eng_civil', 'CF01', 'Aluguel / Escritório', 'custo_fixo', 1),
  ('eng_civil', 'CF02', 'Salários / Pró-labore', 'custo_fixo', 2),
  ('eng_civil', 'CF03', 'Veículos / Combustível', 'custo_fixo', 3),
  ('eng_civil', 'CF04', 'Contabilidade', 'custo_fixo', 4),
  ('eng_civil', 'JU01', 'Juros bancários', 'juros', 1),
  ('eng_civil', 'JU02', 'Multas / Tarifas', 'juros', 2),
  ('eng_civil', 'IN01', 'Investimentos / Equipamentos', 'investimentos', 1),
  ('eng_civil', 'RC01', 'Receita de obras', 'receita', 1),
  ('eng_civil', 'RC02', 'Outras receitas', 'receita', 2),
  -- Hotelaria
  ('hotelaria', 'CV01', 'Amenities / Suprimentos', 'custo_variavel', 1),
  ('hotelaria', 'CV02', 'Lavanderia / Limpeza', 'custo_variavel', 2),
  ('hotelaria', 'CF01', 'Aluguel / Condomínio', 'custo_fixo', 1),
  ('hotelaria', 'CF02', 'Salários / Turnos', 'custo_fixo', 2),
  ('hotelaria', 'CF03', 'Energia / Água', 'custo_fixo', 3),
  ('hotelaria', 'CF04', 'Contabilidade', 'custo_fixo', 4),
  ('hotelaria', 'JU01', 'Juros bancários', 'juros', 1),
  ('hotelaria', 'JU02', 'Multas / Tarifas', 'juros', 2),
  ('hotelaria', 'IN01', 'Investimentos', 'investimentos', 1),
  ('hotelaria', 'RC01', 'Receita de hospedagem', 'receita', 1),
  ('hotelaria', 'RC02', 'Outras receitas', 'receita', 2),
  -- Distribuidoras
  ('distribuidoras', 'CV01', 'Fornecedor / Distribuição', 'custo_variavel', 1),
  ('distribuidoras', 'CV02', 'Frete / Logística', 'custo_variavel', 2),
  ('distribuidoras', 'CF01', 'Aluguel / Depósito', 'custo_fixo', 1),
  ('distribuidoras', 'CF02', 'Salários', 'custo_fixo', 2),
  ('distribuidoras', 'CF03', 'Combustível / Frota', 'custo_fixo', 3),
  ('distribuidoras', 'CF04', 'Contabilidade', 'custo_fixo', 4),
  ('distribuidoras', 'JU01', 'Juros bancários', 'juros', 1),
  ('distribuidoras', 'JU02', 'Multas / Tarifas', 'juros', 2),
  ('distribuidoras', 'IN01', 'Investimentos', 'investimentos', 1),
  ('distribuidoras', 'RC01', 'Receita de vendas', 'receita', 1),
  ('distribuidoras', 'RC02', 'Outras receitas', 'receita', 2)
on conflict (segmento, codigo) do nothing;
