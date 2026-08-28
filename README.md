# ACC Nomad — greenfield

Plataforma de automação contábil que substitui **Lovable** (frontend) e **n8n** (orquestração).

## Stack

| Camada | Tecnologia |
|--------|------------|
| Frontend | Next.js 16 + Tailwind + Supabase Auth |
| Backend | Python FastAPI |
| Banco | Supabase (Postgres + RLS) |
| IA | OpenAI (banco) + Claude (classificação) |
| PDF | PyMuPDF |

## Estrutura

```
Projeto - ACC/
├── frontend/          Next.js dashboard
├── backend/           FastAPI pipeline
├── supabase/          Migrations SQL
└── docs/              Handoff + PDFs exemplo
```

## Setup

### Migrations Supabase (ordem)

1. `001_initial_schema.sql`
2. `002_seed_demo.sql`
3. `003_fornecedores_envios.sql`
4. `004_seed_fornecedores.sql` (opcional)
5. `005_onboarding_plano_contas.sql`
6. `006_reports_suporte.sql`
7. `007_extrato_saldo_validacao.sql`

### Envio PMG (Email / WhatsApp)

O **SMTP é da conta que envia** (escritório contábil / ACC Nomad), não do cliente.  
Os **destinatários** podem usar qualquer provedor: Gmail, Outlook, Yahoo, e-mail corporativo, etc.

Configure na **Vercel** (PMG roda no frontend) ou no `backend/.env`:

```env
# Conta remetente — SMTP_HOST depende de QUEM ENVIA, não de quem recebe:
# Gmail: smtp.gmail.com | Outlook: smtp.office365.com | Yahoo: smtp.mail.yahoo.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=contato@escritorio.com
SMTP_PASSWORD=senha-de-app
EMAIL_FROM=contato@escritorio.com
SUPABASE_SERVICE_ROLE_KEY=...   # só na Vercel

# WhatsApp (Evolution API, Twilio, etc.)
WHATSAPP_API_URL=https://sua-api/send
WHATSAPP_API_TOKEN=token
```

### Anthropic Claude (classificação IA)

1. Crie uma API key em [console.anthropic.com](https://console.anthropic.com/settings/keys)
2. Configure no `backend/.env` (local) e no **Render** (produção):

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-sonnet-4-6
```

3. Reinicie o backend e confira: `GET /health` → `"llm_provider": "anthropic"`
4. Faça upload de um extrato PDF em `/upload`

Sem a chave, usa extrator fallback + fornecedores cadastrados (menos preciso).

1. Crie um projeto em [supabase.com](https://supabase.com)
2. SQL Editor → execute `supabase/migrations/001_initial_schema.sql`
3. Execute `supabase/migrations/002_seed_demo.sql`
4. Copie **URL** e **anon key** (frontend) + **service role key** (backend)

### 2. Backend

**Terminal 1** (PowerShell):

```powershell
cd "D:\Projetos\Projeto - ACC"
.\.venv\Scripts\Activate.ps1
cd backend
uvicorn acc_nomad.main:app --app-dir src --reload
```

Teste: http://localhost:8000/health

> O `.venv` fica na **raiz** do projeto, não dentro de `backend/`.

### 3. Frontend

**Terminal 2** (PowerShell — separado do backend):

```powershell
cd "D:\Projetos\Projeto - ACC\frontend"
npm run dev
```

App: http://localhost:3000

### 4. Vincular usuário à empresa demo

Após criar conta no app, no SQL Editor do Supabase:

```sql
-- Pegue seu user id em Authentication > Users
update public.profiles set role = 'admin' where email = 'seu@email.com';

insert into public.empresa_membros (empresa_id, user_id)
values (
  'a0000000-0000-4000-8000-000000000001',
  'SEU_USER_UUID'
);
```

## Fluxo

1. Login no dashboard
2. Upload PDF em **Upload**
3. Frontend cria registro em `extratos` → chama backend
4. Backend: detecta banco → extrai → classifica → salva em `lancamentos`
5. **Revisão** — confirma ou corrige categorias (plano de contas)
6. **Tesouraria** — lançamentos em espécie (origem TESOURARIA)
7. **PMG** — relatório gerencial + export CSV Fluxo de Caixa

## Deploy (EasyPanel)

Guia completo: **[docs/deploy-easypanel.md](docs/deploy-easypanel.md)**

Resumo:

```powershell
# Testar imagens localmente
copy .env.production.example .env.production
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

No EasyPanel: serviço **Compose** apontando para `docker-compose.prod.yml`, domínios:

- `app.seudominio.com` → frontend (porta 3000)
- `api.seudominio.com` → backend (porta 8000)

## O que foi descartado

- Lovable (Dashboard Nomad)
- n8n (ACC automacao v4)

## Documentação original

- `docs/extracted/ACC Nomad - Documento Técnico de Handoff.txt`
- `docs/EXTRATOS EXEMPLO/` — PDFs para testes
