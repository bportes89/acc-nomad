import type { NaturezaLancamento, PmgResumo } from "@/lib/types";

export type GrupoPmg =
  | "Fornecedor / Revenda"
  | "Custo Variável"
  | "Custo Fixo"
  | "Juros"
  | "Investimentos"
  | "Receita";

export const GRUPOS_PMG: GrupoPmg[] = [
  "Receita",
  "Fornecedor / Revenda",
  "Custo Variável",
  "Custo Fixo",
  "Juros",
  "Investimentos",
];

export interface AccExportRow {
  data: string;
  descricao: string;
  entrada: number | null;
  saida: number | null;
  categoria: string;
  grupoPmg: GrupoPmg;
  banco: string;
  origem: "BANCO" | "TESOURARIA";
  arquivoExtrato: string;
}

export interface AccExportMeta {
  empresaNome: string;
  empresaCnpj: string;
  periodoLabel: string;
  extratosProcessados: number;
  totalLancamentos: number;
}

export function categoriaToGrupoPmg(
  categoria: string | null | undefined,
  natureza: NaturezaLancamento,
): GrupoPmg {
  const cat = (categoria ?? "").toLowerCase();

  if (
    cat.includes("fornecedor") ||
    cat.includes("revenda") ||
    cat.includes("matéria-prima") ||
    cat.includes("materia-prima")
  ) {
    return natureza === "credito" ? "Receita" : "Fornecedor / Revenda";
  }
  if (cat.includes("juros") || cat.includes("multa") || cat.includes("tarifa")) {
    return "Juros";
  }
  if (cat.includes("invest")) return "Investimentos";
  if (
    cat.includes("fixo") ||
    cat.includes("aluguel") ||
    cat.includes("salár") ||
    cat.includes("salari")
  ) {
    return "Custo Fixo";
  }
  if (cat.includes("receita") || natureza === "credito") {
    return "Receita";
  }
  if (cat.includes("variável") || cat.includes("variavel")) {
    return "Custo Variável";
  }

  return "Custo Variável";
}

export function calcularPmgDetalhado(rows: AccExportRow[]): PmgResumo & {
  fornecedor_revenda: number;
} {
  const resumo = {
    receita: 0,
    fornecedor_revenda: 0,
    custo_variavel: 0,
    custo_fixo: 0,
    juros: 0,
    investimentos: 0,
  };

  for (const row of rows) {
    const v = row.saida ?? row.entrada ?? 0;
    switch (row.grupoPmg) {
      case "Receita":
        resumo.receita += row.entrada ?? 0;
        break;
      case "Fornecedor / Revenda":
        resumo.fornecedor_revenda += row.saida ?? 0;
        break;
      case "Custo Variável":
        resumo.custo_variavel += row.saida ?? 0;
        break;
      case "Custo Fixo":
        resumo.custo_fixo += row.saida ?? 0;
        break;
      case "Juros":
        resumo.juros += row.saida ?? 0;
        break;
      case "Investimentos":
        resumo.investimentos += row.saida ?? 0;
        break;
    }
    void v;
  }

  return resumo;
}

export function resultadoLiquido(
  resumo: PmgResumo & { fornecedor_revenda?: number },
): number {
  const fr = resumo.fornecedor_revenda ?? 0;
  return (
    resumo.receita -
    fr -
    resumo.custo_variavel -
    resumo.custo_fixo -
    resumo.juros -
    resumo.investimentos
  );
}
