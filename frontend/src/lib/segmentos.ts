import type { SegmentoEmpresa } from "@/lib/types";

export const SEGMENTOS: { value: SegmentoEmpresa; label: string; descricao: string }[] = [
  { value: "comercio", label: "Comércio / Varejo", descricao: "Lojas, revendas e varejo em geral" },
  { value: "servicos", label: "Serviços", descricao: "Prestadores de serviço e consultorias" },
  { value: "agro", label: "Agro", descricao: "Produção agrícola e insumos rurais" },
  { value: "saude", label: "Saúde", descricao: "Clínicas, consultórios e laboratórios" },
  { value: "gastronomia", label: "Gastronomia", descricao: "Restaurantes, bares e food service" },
  { value: "supermercados", label: "Supermercados", descricao: "Mercados e atacarejos" },
  { value: "eng_civil", label: "Engenharia civil", descricao: "Obras, construtoras e reformas" },
  { value: "hotelaria", label: "Hotelaria", descricao: "Hotéis, pousadas e hospedagem" },
  { value: "distribuidoras", label: "Distribuidoras", descricao: "Atacado e distribuição" },
];

export function segmentoLabel(segmento: SegmentoEmpresa): string {
  return SEGMENTOS.find((s) => s.value === segmento)?.label ?? segmento;
}

export function normalizeCnpj(value: string): string {
  return value.replace(/\D/g, "").slice(0, 14);
}

export function formatCnpj(value: string): string {
  const digits = normalizeCnpj(value);
  if (digits.length <= 2) return digits;
  if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`;
  if (digits.length <= 8) {
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`;
  }
  if (digits.length <= 12) {
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`;
  }
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
}
