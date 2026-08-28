# Deploy ACC Nomad no EasyPanel

Guia para publicar **frontend (Next.js)** + **backend (FastAPI)** no EasyPanel com Docker Compose.

## Pré-requisitos

- Servidor com [EasyPanel](https://easypanel.io) instalado
- Repositório Git do projeto (GitHub, GitLab, etc.)
- Projeto Supabase com migrations **001–007** aplicadas
- Dois subdomínios (recomendado):
  - `app.seudominio.com` → frontend
  - `api.seudominio.com` → backend

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
NEXT_PUBLIC_API_URL=https://api.seudominio.com
CORS_ORIGINS=https://app.seudominio.com

LLM_PROVIDER=auto
GEMINI_API_KEY=...
```

Gere `API_SECRET` com:

```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## 3. EasyPanel — opção A: Compose (recomendado)

1. **Projects → New** → nome `acc-nomad`
2. **Add Service → Compose**
3. **Source:** Git — URL do repositório + branch
4. **Compose file:** `docker-compose.prod.yml`
5. **Environment:** cole todas as variáveis da seção 2
6. **Domains:**
   - Serviço `frontend` → porta `3000` → `app.seudominio.com`
   - Serviço `backend` → porta `8000` → `api.seudominio.com`
7. **Deploy**

### Verificar

```bash
curl https://api.seudominio.com/health
# {"status":"ok","version":"...","llm_provider":"..."}

# Abra no browser
https://app.seudominio.com/login
```

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
| LLM `fallback` no /health | Sem chave Gemini/Groq | Configurar chaves ou aceitar fallback |

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
