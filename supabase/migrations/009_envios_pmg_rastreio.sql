-- Rastreabilidade de envio PMG (handoff P8 — confirmação WhatsApp/Email)

alter table public.envios_pmg
  add column if not exists provider_name text,
  add column if not exists provider_message_id text,
  add column if not exists confirmado_em timestamptz;

create index if not exists idx_envios_pmg_provider_msg
  on public.envios_pmg (provider_message_id)
  where provider_message_id is not null;
