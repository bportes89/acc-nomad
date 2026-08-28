import type { Lancamento, LancamentoExportavel, PmgResumo, TesourariaLancamento } from "@/lib/types";

const CATEGORIA_MAP: Record<string, keyof PmgResumo> = {
  custo_variavel: "custo_variavel",
  fornecedor: "custo_variavel",
  "fornecedor / revenda": "custo_variavel",
  "não classificado": "custo_variavel",
  custo_fixo: "custo_fixo",
  juros: "juros",
  investimentos: "investimentos",
  receita: "receita",
};

function categoriaEfetiva(cat: string | null | undefined): string {
  return (cat ?? "").toLowerCase();
}

function bucketCategoria(cat: string, natureza: string): keyof PmgResumo {
  const key = Object.entries(CATEGORIA_MAP).find(([k]) => cat.includes(k))?.[1];
  if (key) return key;
  return natureza === "credito" ? "receita" : "custo_variavel";
}

export function calcularPmg(
  lancamentos: Lancamento[],
  tesouraria: TesourariaLancamento[] = [],
): PmgResumo {
  const resumo: PmgResumo = {
    custo_variavel: 0,
    custo_fixo: 0,
    juros: 0,
    investimentos: 0,
    receita: 0,
  };

  for (const l of lancamentos) {
    const cat = categoriaEfetiva(l.categoria_corrigida || l.categoria);
    const key = bucketCategoria(cat, l.natureza);
    resumo[key] += l.valor;
  }

  for (const t of tesouraria) {
    const cat = categoriaEfetiva(t.categoria);
    const key = bucketCategoria(cat, t.natureza);
    resumo[key] += t.valor;
  }

  return resumo;
}

export function toExportRows(
  lancamentos: Lancamento[],
  tesouraria: TesourariaLancamento[] = [],
): LancamentoExportavel[] {
  const banco: LancamentoExportavel[] = lancamentos.map((l) => ({
    data: l.data,
    descricao: l.descricao,
    valor: l.valor,
    natureza: l.natureza,
    categoria: l.categoria_corrigida || l.categoria || "Sem categoria",
    origem: l.origem,
  }));

  const caixa: LancamentoExportavel[] = tesouraria.map((t) => ({
    data: t.data,
    descricao: t.descricao,
    valor: t.valor,
    natureza: t.natureza,
    categoria: t.categoria || "Sem categoria",
    origem: "TESOURARIA",
  }));

  return [...banco, ...caixa].sort((a, b) => a.data.localeCompare(b.data));
}
