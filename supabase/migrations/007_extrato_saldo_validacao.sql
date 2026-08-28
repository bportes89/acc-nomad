-- Validação de saldos nos extratos

alter table public.extratos
  add column if not exists saldo_inicial numeric(14, 2),
  add column if not exists saldo_final numeric(14, 2),
  add column if not exists saldo_calculado numeric(14, 2),
  add column if not exists validacao_saldo_ok boolean,
  add column if not exists validacao_detalhes jsonb;

comment on column public.extratos.validacao_saldo_ok is
  'True se saldo_inicial + movimentações ≈ saldo_final (tolerância R$ 0,02)';
