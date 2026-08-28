# WhatsApp PMG — configuração e rastreio

O envio semanal e manual de PMG por WhatsApp roda na **Vercel** (cron + `/api/pmg/enviar`).  
Cada envio bem-sucedido grava `provider_name`, `provider_message_id` e `confirmado_em` na tabela `envios_pmg`.

**Não precisa configurar agora.** O código já está pronto; sem `WHATSAPP_API_URL` o app usa só e-mail e a opção WhatsApp aparece desabilitada no painel PMG. Quando o cliente escolher o provedor (Z-API, Evolution, etc.), basta adicionar as variáveis na Vercel e redeploy — nenhuma alteração de código.

## 1. Migration Supabase

Execute no SQL Editor do Supabase (ou via CLI):

```sql
-- supabase/migrations/009_envios_pmg_rastreio.sql
```

## 2. Variáveis na Vercel

Em **Settings → Environment Variables** do projeto `acc-nomad-chi`:

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `WHATSAPP_PROVIDER` | Não | `generic` (padrão), `evolution` ou `zapi` |
| `WHATSAPP_API_URL` | Sim | URL completa do endpoint de envio de texto |
| `WHATSAPP_API_TOKEN` | Recomendado | Token/API key do provedor |

Após salvar, faça **Redeploy** para aplicar.

## 3. Provedores suportados

### Evolution API

```env
WHATSAPP_PROVIDER=evolution
WHATSAPP_API_URL=https://SUA-EVOLUTION/message/sendText/NOME-INSTANCIA
WHATSAPP_API_TOKEN=sua-api-key-evolution
```

Payload enviado: `{ "number": "5511999999999", "text": "..." }`  
Header: `apikey: <token>`

### Z-API

```env
WHATSAPP_PROVIDER=zapi
WHATSAPP_API_URL=https://api.z-api.io/instances/SUA_INSTANCIA/token/SEU_TOKEN/send-text
WHATSAPP_API_TOKEN=seu-client-token
```

Payload: `{ "phone": "5511999999999", "message": "..." }`  
Header: `Client-Token: <token>`

### Genérico (webhook próprio)

```env
WHATSAPP_PROVIDER=generic
WHATSAPP_API_URL=https://seu-servico.com/send
WHATSAPP_API_TOKEN=opcional
```

Payload: `{ "number": "5511999999999", "message": "..." }`  
Header: `Authorization: Bearer <token>` (se definido)

## 4. Formato do número

Aceita `(11) 99999-9999`, `11999999999` ou `5511999999999`.  
O sistema normaliza para DDI Brasil (`55` + DDD + número).

## 5. Teste manual

1. Acesse **PMG** no app → seção **Enviar PMG**
2. Selecione empresa, canal **WhatsApp**, número de teste
3. Clique **Enviar relatório**
4. Confira o histórico: coluna **Rastreio** deve mostrar o ID retornado pela API

## 6. Agendamento semanal

O cron (`pmg-scheduler`) usa as mesmas variáveis. Agendamentos com canal `whatsapp` em **PMG → Agendamentos** disparam automaticamente na Vercel.

## 7. Backend Render (opcional)

Se usar PMG pelo FastAPI em vez da Vercel, replique as mesmas variáveis em `backend/.env`:

```env
WHATSAPP_PROVIDER=evolution
WHATSAPP_API_URL=...
WHATSAPP_API_TOKEN=...
```
