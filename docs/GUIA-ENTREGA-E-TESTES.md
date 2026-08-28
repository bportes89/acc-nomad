# ACC Nomad — Guia de entrega e testes

> **Versão PDF:** [GUIA-ENTREGA-E-TESTES.pdf](./GUIA-ENTREGA-E-TESTES.pdf)  
> Regenerar: `python backend/scripts/md_to_pdf.py`

Documento consolidado do que foi implementado no greenfield (substituindo Lovable + n8n) e como validar cada funcionalidade.

**Última atualização:** agosto/2026  
**Repositório:** https://github.com/bportes89/acc-nomad

---

## 1. Visão geral

| Item | Detalhe |
|------|---------|
| **Cliente** | ACC — Osvaldo e Nahim |
| **Produto** | ACC Nomad — automação de extratos bancários → classificação → PMG |
| **Frontend (produção)** | https://acc-nomad-chi.vercel.app |
| **Backend (produção)** | https://acc-nomad.onrender.com |
| **Banco de dados** | Supabase (Postgres + Auth + RLS) |
| **IA** | Anthropic Claude (Haiku para classificação rápida; Sonnet disponível) |

### Fluxo principal

```
Login → Upload PDF(s) → Backend processa → Revisão humana → Export XLSX/CSV → PMG → E-mail (opcional WhatsApp)
```

---

## 2. O que foi implementado

### 2.1 Infraestrutura e arquitetura

- **Frontend** Next.js 16 + Tailwind + Supabase Auth (Vercel)
- **Backend** FastAPI + PyMuPDF (Render)
- **Migrations** Supabase versionadas em `supabase/migrations/`
- **Deploy** Vercel (app + cron PMG) + Render (API) — alternativa Docker/EasyPanel em `docs/deploy-easypanel.md`
- Descarte do stack antigo: Lovable (dashboard) e n8n (workflow ACC automacao v4)

### 2.2 Autenticação e acesso

- Login com e-mail/senha (Supabase Auth)
- Recuperação de senha (`/auth/reset-password`)
- Perfis com role (`admin` / usuário) e vínculo empresa ↔ usuário (`empresa_membros`)
- RLS habilitado nas tabelas principais (isolamento por empresa)

### 2.3 Empresas e onboarding

- Cadastro de empresas (CNPJ, nome, segmento)
- Plano de contas por segmento: comércio, saúde, agro, serviços
- Migration `005_onboarding_plano_contas.sql`

**Tela:** `/empresas`

### 2.4 Upload e pipeline de extratos

- Upload de um ou **vários PDFs** consolidados em um único XLSX ACC
- Detecção automática de banco (Bradesco, Sicoob, Sicredi, Unicredi, Itaú, Santander, BB, BASA, Mercado Pago, etc.)
- **Pipeline rápido (padrão):**
  1. Extração local por regex (`fallback_extractor.py`) — Bradesco C/D, Sicoob R$, Mercado Pago, Unicredi/Sicredi linha única
  2. Classificação por regras/keywords (`rule_classifier.py`)
  3. Classificação em lote via Claude Haiku (`generate_json_fast`) só para o restante
  4. Fallback LLM completo apenas se extração local retornar 0 lançamentos
- Match de fornecedores cadastrados
- Ordenação cronológica por banco
- Validação de saldo inicial/final (`saldo_validator.py`) com badge no dashboard
- Mensagens claras para PDF escaneado (sem texto selecionável)
- Processamento em thread (`asyncio.to_thread`) para não bloquear a API

**Telas:** `/upload`, `/dashboard`  
**API:** `POST /api/extratos/processar` (Render)

### 2.5 Revisão humana (feedback loop)

- Lista de lançamentos pendentes de revisão
- Confirmar ou corrigir categoria
- Grava histórico em `revisoes` (base para evolução futura da IA)

**Tela:** `/revisao`

### 2.6 Fornecedores

- CRUD de fornecedores com categoria sugerida
- Usado no match automático durante classificação

**Tela:** `/fornecedores`

### 2.7 Tesouraria (caixa físico)

- Lançamentos em espécie com origem `TESOURARIA`
- Integração no PMG e export XLSX (campo origem `BANCO | TESOURARIA`)
- Tabela `tesouraria_lancamentos`

**Tela:** `/tesouraria`

### 2.8 Exportação Fluxo de Caixa / XLSX ACC

- Download automático após upload (consolidado multi-PDF)
- Export manual CSV e Excel (.xlsx) no PMG
- Abas: lançamentos + resumo PMG
- Colunas: data, descrição, entrada, saída, categoria, grupo PMG, banco, origem

**Arquivos:** `frontend/src/lib/acc-export.ts`, `export-xlsx.ts`

> **Pendente com cliente:** validar layout 100% idêntico ao template XLSX do Osvaldo (handoff).

### 2.9 Relatório PMG

- Painel de Metas Gerenciais (receita, custos, juros, investimentos, resultado)
- Gráfico visual
- Considera apenas lançamentos **revisados** + tesouraria
- Export CSV/XLSX do fluxo aprovado

**Tela:** `/pmg`

### 2.10 Envio PMG por e-mail

- Envio manual (empresa + período + destinatário)
- Histórico de envios em `envios_pmg`
- SMTP configurável (Gmail, Outlook, Yahoo, etc.)

**Requisito Vercel:** `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `SUPABASE_SERVICE_ROLE_KEY`

### 2.11 Agendamento semanal PMG

- Cadastro de agendamentos por empresa (dia da semana, canal, destinatário)
- Cron Vercel: segunda-feira 11:00 UTC (`vercel.json` → `/api/pmg/cron-semanal`)
- Envia PMG do **mês anterior**
- Botão “Testar disparo agora” (usa mês atual)
- Evita reenvio duplicado na mesma semana

**Migration:** `008_pmg_agendamentos.sql`

### 2.12 WhatsApp PMG (código pronto — config opcional)

- Cliente WhatsApp com suporte Evolution API, Z-API e genérico
- Rastreio: `provider_name`, `provider_message_id`, `confirmado_em`
- UI desabilita WhatsApp até `WHATSAPP_API_URL` existir na Vercel
- **Não exige configuração agora** — ver `docs/WHATSAPP-PMG.md`

**Migration:** `009_envios_pmg_rastreio.sql`

### 2.13 Suporte / Report de erro

- Formulário de ticket vinculado à empresa
- Listagem de reports em `reports_erro`

**Tela:** `/suporte`  
**Migration:** `006_reports_suporte.sql`

### 2.14 Ferramentas GoLive / QA

- Script benchmark: `backend/scripts/benchmark_extrato.py`
- Gerador PDF sintético Bradesco 29p: `gerar_extrato_bradesco_teste.py`
- Gerador PDF sintético Unicredi: `gerar_extrato_unicredi_teste.py`
- Critérios objetivos: `docs/CRITERIOS-GOLIVE.md`
- Testes pytest em `backend/tests/`

### 2.15 Resultados de testes conhecidos

| Extrato | Resultado |
|---------|-----------|
| Sicoob (produção) | ~45 lançamentos — fluxo upload → revisão → XLSX OK |
| Bradesco sintético 29p | ~232 lançamentos — benchmark `passed: true` |
| Unicredi sintético | ~50 lançamentos — benchmark OK |
| Unicredi real (escaneado) | 0 lançamentos — esperado sem OCR |
| Bradesco real (Drive cliente) | Não testado — arquivo requer permissão |

---

## 3. O que ainda está pendente (fora do escopo imediato)

| Item | Observação |
|------|------------|
| WhatsApp PMG em produção | Configurar com cliente (Z-API / Evolution) |
| Template XLSX Osvaldo | Validar colunas/abas com planilha real do cliente |
| PDF 100% imagem (OCR) | Unicredi escaneado e similares |
| Bradesco real 29p | Obter PDF do cliente e validar em produção |
| Auditoria RLS/LGPD formal | Antes de escala (100 clientes) |
| Teste de carga 400 docs/mês | Pós-GoLive |
| Feedback loop treinando modelo | Revisões gravadas, retreino não implementado |

---

## 4. Ambiente e variáveis

### 4.1 Supabase

| Variável | Onde |
|----------|------|
| `NEXT_PUBLIC_SUPABASE_URL` | Vercel + frontend local |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Vercel + frontend local |
| `SUPABASE_SERVICE_ROLE_KEY` | Vercel (PMG) + Render (backend) |

### 4.2 Backend (Render / local)

```env
SUPABASE_URL=https://SEU_PROJETO.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
API_SECRET=mesma-chave-no-frontend
CORS_ORIGINS=https://acc-nomad-chi.vercel.app

LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6
ANTHROPIC_MODEL_FAST=claude-haiku-4-5
```

### 4.3 Frontend (Vercel / local)

```env
NEXT_PUBLIC_API_URL=https://acc-nomad.onrender.com
API_URL=https://acc-nomad.onrender.com
API_SECRET=...

# PMG e-mail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
EMAIL_FROM=...

# Cron (opcional)
CRON_SECRET=...

# WhatsApp (opcional — depois)
WHATSAPP_PROVIDER=generic
WHATSAPP_API_URL=
WHATSAPP_API_TOKEN=
```

---

## 5. Migrations Supabase (ordem)

Execute no SQL Editor na ordem:

1. `001_initial_schema.sql` — schema base, RLS, tabelas principais
2. `002_seed_demo.sql` — empresa demo
3. `003_fornecedores_envios.sql` — fornecedores, envios PMG
4. `004_seed_fornecedores.sql` — (opcional) dados demo
5. `005_onboarding_plano_contas.sql` — plano de contas por segmento
6. `006_reports_suporte.sql` — tickets de suporte
7. `007_extrato_saldo_validacao.sql` — validação de saldo
8. `008_pmg_agendamentos.sql` — agendamento semanal
9. `009_envios_pmg_rastreio.sql` — rastreio WhatsApp/e-mail
10. `010_empresas_rls_onboarding.sql` — permissão cadastro de empresas (RLS)

### Vincular usuário à empresa demo

Após criar conta no app:

```sql
-- Authentication > Users → copie o UUID
UPDATE public.profiles SET role = 'admin' WHERE email = 'seu@email.com';

INSERT INTO public.empresa_membros (empresa_id, user_id)
VALUES (
  'a0000000-0000-4000-8000-000000000001',
  'SEU_USER_UUID'
);
```

---

## 6. Rodar localmente

### Terminal 1 — Backend

```powershell
cd "D:\Projetos\Projeto - ACC"
.\.venv\Scripts\Activate.ps1
cd backend
# Configure backend/.env (copie de .env.example)
uvicorn acc_nomad.main:app --app-dir src --reload
```

Confirme: http://localhost:8000/health → `"llm_provider": "anthropic"` (se chave configurada)

### Terminal 2 — Frontend

```powershell
cd "D:\Projetos\Projeto - ACC\frontend"
# Configure .env.local
npm run dev
```

App: http://localhost:3000

---

## 7. Como testar — roteiro completo

### 7.1 Checklist rápido (15 min — demo cliente)

| # | Passo | O que verificar |
|---|-------|-----------------|
| 1 | Abrir https://acc-nomad-chi.vercel.app | Login funciona |
| 2 | `/empresas` | Empresa cadastrada, segmento escolhido |
| 3 | `/upload` | Enviar PDF Sicoob ou Bradesco sintético |
| 4 | Aguardar processamento | Mensagem de sucesso + download XLSX |
| 5 | `/dashboard` | Extrato com status processado, badge saldo |
| 6 | `/revisao` | Lançamentos listados, corrigir 1 categoria |
| 7 | `/tesouraria` | Inserir lançamento em espécie (opcional) |
| 8 | `/pmg` | Gráfico e totais batem com revisados |
| 9 | `/pmg` → Enviar PMG | E-mail chega (se SMTP configurado) |
| 10 | `/pmg` → Excel | Download .xlsx abre corretamente |

### 7.2 Teste detalhado por módulo

#### Login e recuperação de senha

1. Acesse `/login` → crie conta ou entre
2. “Esqueci minha senha” → e-mail de reset (Supabase Auth)
3. Complete reset em `/auth/reset-password`

#### Upload de extrato

1. `/upload` → selecione empresa e segmento
2. Selecione 1+ PDFs
3. Opcional: instrução personalizada para a IA
4. Envie e aguarde (~30s–2min)
5. **Esperado:** XLSX baixa automaticamente; extrato aparece no dashboard

**PDFs no repositório:**

- `docs/EXTRATOS EXEMPLO/bradesco-sintetico-29p.pdf`
- `docs/EXTRATOS EXEMPLO/unicredi-sintetico-jul26.pdf`

**Gerar Bradesco sintético:**

```powershell
cd backend
python scripts/gerar_extrato_bradesco_teste.py
```

#### Revisão

1. `/revisao` → filtre por empresa/período
2. Confirme lançamento ou altere categoria
3. **Esperado:** `revisado = true`; registro em `revisoes`

#### Tesouraria

1. `/tesouraria` → nova entrada (data, valor, natureza, categoria)
2. **Esperado:** origem `TESOURARIA`; aparece no PMG e no XLSX

#### PMG e exportação

1. `/pmg` → selecione empresa (não “Todas”) e mês
2. Confira gráfico e totais
3. Baixe CSV e Excel
4. Envie por e-mail (destinatário qualquer: Gmail, Outlook, etc.)

#### Agendamento semanal

1. `/pmg` → seção “Envio semanal automático”
2. Cadastre: empresa, dia, canal e-mail, destinatário
3. “Testar disparo agora” → ver mensagem com contagem enviados/erros
4. Cron real: segunda 08:00 BRT (11:00 UTC)

#### Suporte

1. `/suporte` → preencha report de erro
2. **Esperado:** ticket na listagem

#### WhatsApp (quando configurado)

1. Configure vars na Vercel (ver `docs/WHATSAPP-PMG.md`)
2. Redeploy
3. `/pmg` → canal WhatsApp habilitado
4. Envie teste → histórico mostra ID na coluna Rastreio

---

## 8. Testes automatizados (backend)

```powershell
cd backend
python -m pytest tests/ -q
```

Testes principais:

| Arquivo | O que cobre |
|---------|-------------|
| `test_fallback_extractor.py` | Extração local por banco |
| `test_bradesco_golive.py` | Critérios GoLive Bradesco |
| `test_saldo_validator.py` | Validação de saldo |
| `test_whatsapp_client.py` | Normalização de número |
| `test_pmg_scheduler.py` | Lógica agendamento |
| `test_llm_providers.py` | Providers LLM |

---

## 9. Benchmark GoLive (extrato)

```powershell
cd backend

# Com IA (Anthropic configurada)
python scripts/benchmark_extrato.py "..\docs\EXTRATOS EXEMPLO\bradesco-sintetico-29p.pdf"

# Só extração local (sem API key)
python scripts/benchmark_extrato.py "..\docs\EXTRATOS EXEMPLO\bradesco-sintetico-29p.pdf" --local-only
```

**Aceite:** JSON com `"passed": true`.

Critérios detalhados: `docs/CRITERIOS-GOLIVE.md`

| Critério | Limite |
|----------|--------|
| Lançamentos | ≥ 1 |
| Densidade | ≥ 0,5 lanç./página |
| Classificação | ≥ 70% fora de “Não classificado (fallback)” |
| Tempo | ≤ 90 segundos |
| PDF escaneado | Detectado se texto < 500 chars |

---

## 10. Testes de API (curl)

### Health

```powershell
curl https://acc-nomad.onrender.com/health
```

### Processar extrato (requer token Supabase ou API_SECRET)

O upload normal usa o frontend com JWT do usuário logado. Para teste direto na API, use Postman ou o fluxo web.

### PMG manual (API_SECRET)

```powershell
curl -X POST https://acc-nomad-chi.vercel.app/api/pmg/enviar `
  -H "Content-Type: application/json" `
  -d '{"empresa_id":"...","empresa_nome":"Demo","periodo":"2026-01","canal":"email","destinatario":"teste@email.com","resumo":{"receita":1000,"custo_variavel":200,"custo_fixo":300,"juros":10,"investimentos":0}}'
```

---

## 11. Troubleshooting

| Problema | Causa provável | Solução |
|----------|----------------|---------|
| “Conectando ao servidor…” longo | Render free tier cold start | Aguardar 30–60s; abrir `/health` antes |
| “Backend indisponível” | `NEXT_PUBLIC_API_URL` errada na Vercel | Definir URL Render + redeploy |
| “PDF escaneado” | PDF é imagem, sem texto | Baixar PDF nativo do internet banking |
| 0 lançamentos Unicredi real | PDF escaneado | Deixar de lado ou implementar OCR |
| “SMTP não configurado” | Vars e-mail ausentes na Vercel | Configurar SMTP_* + EMAIL_FROM |
| WhatsApp desabilitado | Normal sem `WHATSAPP_API_URL` | Configurar depois com cliente |
| Sem dados no PMG | Lançamentos não revisados | Revisar em `/revisao` |
| Sem permissão ao criar empresa (RLS) | Migration 005/010 não aplicada | Rodar `010_empresas_rls_onboarding.sql` no Supabase |

---

## 12. Estrutura do repositório

```
Projeto - ACC/
├── frontend/                 Next.js (dashboard)
│   ├── src/app/(app)/        Páginas: upload, revisao, pmg, tesouraria…
│   ├── src/app/api/          Rotas PMG, cron, proxy extratos
│   └── src/lib/              Export XLSX, PMG, processamento
├── backend/
│   ├── src/acc_nomad/        Pipeline, classificador, extrator
│   ├── scripts/              Benchmark e geradores de PDF teste
│   └── tests/                Testes pytest
├── supabase/migrations/      Schema SQL
└── docs/
    ├── GUIA-ENTREGA-E-TESTES.md   ← este documento
    ├── CRITERIOS-GOLIVE.md
    ├── WHATSAPP-PMG.md
    └── EXTRATOS EXEMPLO/          PDFs para teste
```

---

## 13. Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| `README.md` | Setup rápido |
| `docs/CRITERIOS-GOLIVE.md` | Critérios de aceite Item 7 |
| `docs/WHATSAPP-PMG.md` | Config WhatsApp (quando cliente definir) |
| `docs/deploy-easypanel.md` | Deploy Docker/EasyPanel |
| `docs/extracted/ACC Nomad - Documento Técnico de Handoff.txt` | Handoff original |

---

## 14. Roteiro sugerido para entrega ao cliente

1. **Demo ao vivo** — checklist seção 7.1 (15 min)
2. **Pedir ao Osvaldo/Nahim:**
   - Template XLSX oficial para validação
   - Extrato Bradesco real (29 páginas) por e-mail
3. **Rodar benchmark** no PDF real antes da demo
4. **Validar e-mail PMG** com destinatário do escritório
5. **Deixar WhatsApp** para fase 2 (provedor + número do escritório)
6. **Registrar pendências** OCR e carga se cliente exigir escala imediata

---

*Documento gerado para handoff técnico e QA. Para dúvidas operacionais, consulte também a gravação Fireflies do handoff ACC (Paschoim).*
