insert into public.fornecedores (empresa_id, nome, categoria_sugerida)
select 'a0000000-0000-4000-8000-000000000001', nome, cat from (values
  ('KLEverson Scheffer', 'Fornecedor / Revenda'),
  ('MUNICIPIO DE CUIABA', 'Custo Fixo'),
  ('UBER', 'Custo Variável'),
  ('JOAO DOUGLAS PEREIRA', 'Receita de vendas')
) as v(nome, cat)
where not exists (
  select 1 from public.fornecedores f
  where f.empresa_id = 'a0000000-0000-4000-8000-000000000001' and f.nome = v.nome
);
