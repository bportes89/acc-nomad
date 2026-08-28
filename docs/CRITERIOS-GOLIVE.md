# Critérios GoLive — ACC Nomad (Item 7)

Documento de aceite para **vender/entregar** o produto. Use o script de benchmark antes de apresentar ao cliente.

## Como testar

```powershell
cd backend
python scripts/benchmark_extrato.py "..\docs\EXTRATOS EXEMPLO\Copy of SICOOB - CR PIX JAN 25.pdf"
python scripts/benchmark_extrato.py "C:\caminho\extrato-bradesco-29p.pdf"
```

Opção sem LLM (só extração local):

```powershell
python scripts/benchmark_extrato.py extrato.pdf --local-only
```

Saída JSON com `"passed": true/false` e lista de `failures`.

---

## Critérios objetivos (automáticos)

| Critério | Limite | Motivo |
|----------|--------|--------|
| Lançamentos extraídos | ≥ 1 | Pipeline funcionou |
| Densidade | ≥ 0,5 lanç./página | Bradesco 29p → mín. ~15 txs |
| Classificação | ≥ **70%** fora de "Não classificado (fallback)" | Vendável com revisão leve |
| Tempo total | ≤ **90 segundos** | Experiência comercial |
| Saldo | OK ou aviso parcial | Divergência não bloqueia, mas alerta |
| PDF escaneado | Texto ≥ 500 chars (se >3 págs) | Detecta OCR necessário |

---

## Checklist manual (você valida)

### Upload → Revisão → PMG

- [ ] Upload múltiplo PDF → XLSX baixa automaticamente
- [ ] Revisão lista lançamentos com categorias IA
- [ ] Confirmar/corrigir grava feedback em `revisoes`
- [ ] PMG reflete lançamentos **revisados**
- [ ] Envio e-mail PMG funciona
- [ ] Agendamento semanal dispara (teste manual)

### Teste de ouro — Bradesco 29 páginas

PDF de referência (cliente Osvaldo):

https://drive.google.com/file/d/1YbgklNMpB3YzQtysIQhQMnCwjQWfJjZw/view

1. Baixe o PDF completo (não preview do Drive)
2. Rode `benchmark_extrato.py`
3. Faça upload em produção e compare contagem de lançamentos
4. **Aceite:** contagem similar ao extrato manual + tempo < 90s

### Teste Sicoob (já validado em produção)

- 45 lançamentos extraídos
- Fluxo upload → revisão → XLSX OK

---

## O que ainda fica fora deste sprint

- WhatsApp PMG (config API)
- OCR para PDF 100% imagem
- Feedback loop treinando modelo
- Teste carga 400 docs/mês
- Auditoria LGPD formal

---

## Variáveis Render (Item 7)

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6
ANTHROPIC_MODEL_FAST=claude-haiku-4-5
```

Pipeline atual: **extração local (ms) + regras + Haiku só para o restante**.
