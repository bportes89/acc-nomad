import * as XLSX from "xlsx";
import {
  type AccExportMeta,
  type AccExportRow,
  calcularPmgDetalhado,
  categoriaToGrupoPmg,
  resultadoLiquido,
} from "@/lib/pmg-categories";
import type { Lancamento, TesourariaLancamento } from "@/lib/types";

type ExtratoJoin = { banco: string | null; nome_arquivo: string };

export function lancamentosToAccRows(
  lancamentos: (Lancamento & { extratos?: ExtratoJoin | null })[],
): AccExportRow[] {
  return lancamentos
    .map((l) => {
      const categoria = l.categoria_corrigida || l.categoria || "Sem categoria";
      const grupoPmg = categoriaToGrupoPmg(categoria, l.natureza);
      return {
        data: l.data,
        descricao: l.descricao,
        entrada: l.natureza === "credito" ? l.valor : null,
        saida: l.natureza === "debito" ? l.valor : null,
        categoria,
        grupoPmg,
        banco: (l.extratos?.banco ?? "—").toUpperCase(),
        origem: l.origem,
        arquivoExtrato: l.extratos?.nome_arquivo ?? "—",
      };
    })
    .sort(
      (a, b) =>
        a.data.localeCompare(b.data) || a.descricao.localeCompare(b.descricao),
    );
}

export function tesourariaToAccRows(items: TesourariaLancamento[]): AccExportRow[] {
  return items.map((t) => {
    const categoria = t.categoria || "Sem categoria";
    const grupoPmg = categoriaToGrupoPmg(categoria, t.natureza);
    return {
      data: t.data,
      descricao: t.descricao,
      entrada: t.natureza === "credito" ? t.valor : null,
      saida: t.natureza === "debito" ? t.valor : null,
      categoria,
      grupoPmg,
      banco: "TESOURARIA",
      origem: "TESOURARIA",
      arquivoExtrato: "—",
    };
  });
}

export function exportAccConsolidadoXlsx(
  rows: AccExportRow[],
  meta: AccExportMeta,
  filename: string,
) {
  const resumo = calcularPmgDetalhado(rows);
  const resultado = resultadoLiquido(resumo);

  const pmgRows: (string | number | null)[][] = [
    ["ACC NOMAD — Painel de Metas Gerenciais (PMG)"],
    ["Empresa", meta.empresaNome],
    ["CNPJ", meta.empresaCnpj],
    ["Período", meta.periodoLabel],
    ["Extratos processados", meta.extratosProcessados],
    ["Total de lançamentos", meta.totalLancamentos],
    [],
    ["Grupo PMG", "Valor (R$)"],
    ["RECEITAS", ""],
    ["Receita", resumo.receita],
    [],
    ["DESPESAS", ""],
    ["Fornecedor / Revenda", resumo.fornecedor_revenda],
    ["Custo Variável", resumo.custo_variavel],
    ["Custo Fixo", resumo.custo_fixo],
    ["Juros e Tarifas", resumo.juros],
    ["Investimentos", resumo.investimentos],
    [],
    ["RESULTADO LÍQUIDO", resultado],
  ];

  const fluxoHeader = [
    "Data",
    "Descrição",
    "Entrada (R$)",
    "Saída (R$)",
    "Grupo PMG",
    "Categoria",
    "Banco",
    "Origem",
    "Arquivo Extrato",
  ];
  const fluxoRows = rows.map((r) => [
    formatDateBr(r.data),
    r.descricao,
    r.entrada,
    r.saida,
    r.grupoPmg,
    r.categoria,
    r.banco,
    r.origem,
    r.arquivoExtrato,
  ]);

  const porBanco = aggregateByBank(rows);
  const bancoHeader = [
    "Banco",
    "Entradas (R$)",
    "Saídas (R$)",
    "Saldo (R$)",
    "Lançamentos",
  ];
  const bancoRows = porBanco.map((b) => [
    b.banco,
    b.entradas,
    b.saidas,
    b.entradas - b.saidas,
    b.count,
  ]);

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, sheetFromAoA(pmgRows), "PMG");
  XLSX.utils.book_append_sheet(
    wb,
    sheetFromAoA([fluxoHeader, ...fluxoRows]),
    "Fluxo de Caixa Aprovado",
  );
  XLSX.utils.book_append_sheet(
    wb,
    sheetFromAoA([bancoHeader, ...bancoRows]),
    "Resumo por Banco",
  );

  XLSX.writeFile(wb, filename);
}

export function exportFluxoCaixaXlsxFromLegacy(
  rows: import("@/lib/types").LancamentoExportavel[],
  _resumo: import("@/lib/types").PmgResumo,
  filename: string,
  meta?: Partial<AccExportMeta>,
) {
  const accRows: AccExportRow[] = rows.map((r) => ({
    data: r.data,
    descricao: r.descricao,
    entrada: r.natureza === "credito" ? r.valor : null,
    saida: r.natureza === "debito" ? r.valor : null,
    categoria: r.categoria,
    grupoPmg: categoriaToGrupoPmg(r.categoria, r.natureza),
    banco: r.origem === "TESOURARIA" ? "TESOURARIA" : "—",
    origem: r.origem,
    arquivoExtrato: "—",
  }));

  exportAccConsolidadoXlsx(accRows, {
    empresaNome: meta?.empresaNome ?? "Consolidado",
    empresaCnpj: meta?.empresaCnpj ?? "—",
    periodoLabel: meta?.periodoLabel ?? "—",
    extratosProcessados: meta?.extratosProcessados ?? 0,
    totalLancamentos: accRows.length,
  }, filename);
}

function sheetFromAoA(data: (string | number | null)[][]) {
  return XLSX.utils.aoa_to_sheet(data);
}

function formatDateBr(iso: string) {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function aggregateByBank(rows: AccExportRow[]) {
  const map = new Map<
    string,
    { entradas: number; saidas: number; count: number }
  >();

  for (const r of rows) {
    const cur = map.get(r.banco) ?? { entradas: 0, saidas: 0, count: 0 };
    cur.entradas += r.entrada ?? 0;
    cur.saidas += r.saida ?? 0;
    cur.count += 1;
    map.set(r.banco, cur);
  }

  return Array.from(map.entries())
    .map(([banco, v]) => ({ banco, ...v }))
    .sort((a, b) => a.banco.localeCompare(b.banco));
}
