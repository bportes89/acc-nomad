import type { LancamentoExportavel } from "@/lib/types";

export function exportFluxoCaixaCsv(rows: LancamentoExportavel[], filename: string) {
  const header = ["Data", "Descricao", "Valor", "Natureza", "Categoria", "Origem"];
  const lines = [
    header.join(";"),
    ...rows.map((r) =>
      [
        r.data,
        `"${r.descricao.replace(/"/g, '""')}"`,
        r.valor.toFixed(2).replace(".", ","),
        r.natureza,
        `"${r.categoria.replace(/"/g, '""')}"`,
        r.origem,
      ].join(";"),
    ),
  ];

  const blob = new Blob(["\uFEFF" + lines.join("\n")], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
