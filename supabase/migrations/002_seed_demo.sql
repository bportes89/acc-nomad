-- Dados demo para desenvolvimento
-- Após criar conta no app, vincule seu usuário à empresa demo:

insert into public.empresas (id, nome, cnpj, segmento, instrucao_personalizada)
values (
  'a0000000-0000-4000-8000-000000000001',
  'Loja Demo ACC',
  '00000000000191',
  'comercio',
  'Priorizar categorias de fornecedor e receita de vendas.'
)
on conflict (cnpj) do nothing;

-- Vincular usuário (substitua USER_ID pelo uuid de auth.users):
-- insert into public.empresa_membros (empresa_id, user_id)
-- values ('a0000000-0000-4000-8000-000000000001', 'USER_ID');

-- Tornar primeiro usuário admin (substitua USER_ID):
-- update public.profiles set role = 'admin' where id = 'USER_ID';
