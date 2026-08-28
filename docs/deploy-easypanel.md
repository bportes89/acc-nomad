# Deploy ACC Nomad no EasyPanel

Guia para publicar **frontend (Next.js)** + **backend (FastAPI)** no EasyPanel com Docker Compose.

## Pré-requisitos

- Servidor VPS com Ubuntu (22.04 ou 24.04) — **mín. 2 GB RAM**
- [EasyPanel](https://easypanel.io) instalado (veja seção 0 abaixo)
- Repositório Git: `https://github.com/bportes89/acc-nomad.git`
- Projeto Supabase com migrations **001–007** aplicadas
- Dois subdomínios (recomendado):
  - `app.seudominio.com` → frontend
  - `api.seudominio.com` → backend

---

## 0. Instalar EasyPanel (primeira vez)

Se você **ainda não tem servidor**, contrate um VPS em qualquer provedor (Hostinger, DigitalOcean, Hetzner, Contabo, etc.):

| Recurso | Mínimo recomendado |
|---------|-------------------|
| SO | Ubuntu 22.04 ou 24.04 (instalação limpa) |
| RAM | 2 GB (4 GB confortável) |
| Disco | 20 GB SSD |
| Portas | 22 (SSH), 80, 443, 3000 (painel) |

### 0.1 Acessar o servidor via SSH

No PowerShell (substitua pelo IP que o provedor enviou):

```powershell
ssh root@SEU_IP_DO_SERVIDOR
```

### 0.2 Instalar EasyPanel (comando oficial)

No servidor, como **root**:

```bash
curl -sSL https://get.easypanel.io | sh
```

O script instala Docker + EasyPanel automaticamente (leva 2–5 min).

Documentação oficial: https://easypanel.io/docs

### 0.3 Abrir o painel

No navegador:

```
http://SEU_IP_DO_SERVIDOR:3000
```

Na primeira vez, crie sua **conta admin** (e-mail + senha).

> Depois você pode apontar um domínio tipo `panel.seudominio.com` para o IP e ativar HTTPS no EasyPanel.

### 0.4 Firewall (se o painel não abrir)

No servidor:

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw allow 3000
ufw enable
```

Também libere essas portas no **painel do provedor** (Security Group / Firewall do VPS).

---

## 1. Supabase (antes do deploy)

No **SQL Editor**, execute na ordem:

1. `supabase/migrations/001_initial_schema.sql`
2. `002_seed_demo.sql` (opcional)
3. `003_fornecedores_envios.sql`
4. `004_seed_fornecedores.sql` (opcional)
5. `005_onboarding_plano_contas.sql`
6. `006_reports_suporte.sql`
7. `007_extrato_saldo_validacao.sql`
8. `008_pmg_agendamentos.sql` (envio semanal automático do PMG)

### Auth — URLs de produção

**Authentication → URL Configuration**

| Campo | Valor |
|-------|-------|
| Site URL | `https://app.seudominio.com` |
| Redirect URLs | `https://app.seudominio.com/auth/callback` |
| | `https://app.seudominio.com/auth/reset-password` |

---

## 2. Variáveis de ambiente

Copie `.env.production.example` e preencha:

```env
FRONTEND_URL=https://app.seudominio.com
API_PUBLIC_URL=https://api.seudominio.com

SUPABASE_URL=https://SEU_PROJETO.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_...
NEXT_PUBLIC_SUPABASE_URL=https://SEU_PROJETO.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...

API_SECRET=uma-chave-longa-aleatoria-min-32-chars
CRON_SECRET=outra-chave-para-vercel-cron
NEXT_PUBLIC_API_URL=https://api.seudominio.com
CORS_ORIGINS=https://app.seudominio.com

LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

Gere `API_SECRET` com:

```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## 3. EasyPanel — deploy do ACC Nomad (Compose)

Repositório: **https://github.com/bportes89/acc-nomad** (branch `main`)

1. **Projects → Create** → nome `acc-nomad`
2. **Add Service → Compose**
3. **Source → GitHub**
   - Conecte sua conta GitHub (autorize o EasyPanel)
   - Repo: `bportes89/acc-nomad`
   - Branch: `main`
4. **Compose file:** `docker-compose.prod.yml`
5. **Environment** — adicione cada variável (botão Add):

   | Variável | Valor |
   |----------|-------|
   | `SUPABASE_URL` | URL do Supabase |
   | `SUPABASE_SERVICE_ROLE_KEY` | chave secret do Supabase |
   | `NEXT_PUBLIC_SUPABASE_URL` | mesma URL |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | anon key |
   | `NEXT_PUBLIC_API_URL` | `https://api.seudominio.com` |
   | `API_SECRET` | chave longa (mesma nos dois serviços) |
   | `CORS_ORIGINS` | `https://app.seudominio.com` |
   | `LLM_PROVIDER` | `anthropic` |
   | `ANTHROPIC_API_KEY` | chave em console.anthropic.com |
   | `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` (opcional) |

6. **Domains** (aba Domains de cada serviço no Compose):
   - `frontend` → porta **3000** → `app.seudominio.com` → Enable HTTPS
   - `backend` → porta **8000** → `api.seudominio.com` → Enable HTTPS
7. **Deploy** (botão verde)

### DNS (no Registro.br, Cloudflare, etc.)

Antes dos domínios funcionarem, crie registros **A** apontando para o IP do VPS:

| Registro | Tipo | Valor |
|----------|------|-------|
| `app` | A | IP do VPS |
| `api` | A | IP do VPS |

---

## 4. EasyPanel — opção B: dois Apps separados

Use se preferir deploy independente de frontend e backend.

### Backend (App)

| Campo | Valor |
|-------|-------|
| Build | Dockerfile em `backend/` |
| Port | 8000 |
| Domain | `api.seudominio.com` |
| Env | `SUPABASE_*`, `API_SECRET`, `CORS_ORIGINS`, chaves LLM, SMTP |

Health check: `GET /health`

### Frontend (App)

| Campo | Valor |
|-------|-------|
| Build | Dockerfile em `frontend/` |
| Port | 3000 |
| Domain | `app.seudominio.com` |
| Build args | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL` |
| Runtime env | `API_SECRET`, `API_URL=https://api.seudominio.com` |

> **Build args** são obrigatórios no frontend — variáveis `NEXT_PUBLIC_*` entram no bundle no build.

---

## 5. Teste pós-deploy

1. Login em `https://app.seudominio.com`
2. **Empresas** → cadastre ou vincule empresa
3. **Upload** → envie PDF de `docs/EXTRATOS EXEMPLO/`
4. Dashboard → extrato `processado` + badge de saldo
5. `/health` do backend → `llm_provider` esperado

---

## 6. Troubleshooting

| Problema | Causa provável | Solução |
|----------|----------------|---------|
| Login redireciona com `missing_env` | `NEXT_PUBLIC_SUPABASE_*` ausentes no build | Rebuild frontend com build args |
| Upload falha 401 | `API_SECRET` diferente entre front e back | Igualar nos dois serviços |
| Upload falha 422 Supabase | `SUPABASE_SERVICE_ROLE_KEY` inválida | Corrigir env do backend |
| CORS error | Origem não listada | `CORS_ORIGINS=https://app.seudominio.com` |
| Recuperar senha não funciona | Redirect URL no Supabase | Adicionar URLs da seção 1 |
| LLM `fallback` no /health | Sem `ANTHROPIC_API_KEY` no Render | Definir `LLM_PROVIDER=anthropic` + chave |

---

## 7. Deploy local (testar imagens antes)

```powershell
cd "D:\Projetos\Projeto - ACC"
copy .env.production.example .env.production
# Edite .env.production

docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

- Frontend: http://localhost:3000 (mapeie portas no compose se necessário)
- Backend: http://localhost:8000/health

---

## 8. Atualizações

1. Push no Git
2. EasyPanel → **Redeploy** no serviço Compose ou Apps
3. Frontend precisa **rebuild** quando mudar `NEXT_PUBLIC_*`
4. Backend reinicia só com novas env vars ou código Python

---

## Arquitetura em produção

```
Usuário → app.seudominio.com (Next.js)
              ↓ API routes (/api/extratos/processar)
         api.seudominio.com ou backend:8000 (FastAPI)
              ↓ service role
         Supabase (Postgres + Auth)
```

O n8n **não** faz parte deste deploy — pipeline roda 100% no FastAPI.
