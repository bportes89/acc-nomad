export type SegmentoEmpresa =
  | "comercio"
  | "servicos"
  | "agro"
  | "saude"
  | "gastronomia"
  | "supermercados"
  | "eng_civil"
  | "hotelaria"
  | "distribuidoras";

export type ExtratoStatus =
  | "pendente"
  | "processando"
  | "processado"
  | "erro"
  | "revisado";

export type NaturezaLancamento = "credito" | "debito";

export interface Empresa {
  id: string;
  nome: string;
  cnpj: string;
  segmento: SegmentoEmpresa;
  instrucao_personalizada: string | null;
  ativo: boolean;
}

export interface Fornecedor {
  id: string;
  empresa_id: string;
  nome: string;
  categoria_sugerida: string | null;
  telefone: string | null;
}

export interface PlanoConta {
  id: string;
  segmento: SegmentoEmpresa;
  codigo: string;
  nome: string;
  categoria_pai: string | null;
}

export interface Extrato {
  id: string;
  empresa_id: string;
  nome_arquivo: string;
  banco: string | null;
  status: ExtratoStatus;
  total_lancamentos: number;
  erro_mensagem: string | null;
  saldo_inicial: number | null;
  saldo_final: number | null;
  saldo_calculado: number | null;
  validacao_saldo_ok: boolean | null;
  validacao_detalhes: SaldoValidacaoDetalhes | null;
  created_at: string;
  processed_at: string | null;
}

export interface SaldoValidacaoDetalhes {
  ok: boolean;
  saldo_inicial: number | null;
  saldo_final: number | null;
  saldo_calculado: number | null;
  delta: number | null;
  warnings: string[];
}

export interface Lancamento {
  id: string;
  extrato_id: string;
  empresa_id: string;
  data: string;
  descricao: string;
  valor: number;
  natureza: NaturezaLancamento;
  categoria: string | null;
  categoria_corrigida: string | null;
  origem: "BANCO" | "TESOURARIA";
  revisado: boolean;
}

export interface TesourariaLancamento {
  id: string;
  empresa_id: string;
  data: string;
  descricao: string;
  valor: number;
  natureza: NaturezaLancamento;
  categoria: string | null;
  origem: "TESOURARIA";
}

export interface PmgResumo {
  custo_variavel: number;
  custo_fixo: number;
  juros: number;
  investimentos: number;
  receita: number;
}

export interface EnvioPmg {
  id: string;
  empresa_id: string;
  periodo_inicio: string;
  periodo_fim: string;
  canal: "email" | "whatsapp";
  destinatario: string;
  status: "enviado" | "erro" | "pendente";
  erro_mensagem: string | null;
  created_at: string;
}

export interface LancamentoExportavel {
  data: string;
  descricao: string;
  valor: number;
  natureza: NaturezaLancamento;
  categoria: string;
  origem: "BANCO" | "TESOURARIA";
}

export type ReportErroCategoria =
  | "extrato"
  | "classificacao"
  | "pmg"
  | "login"
  | "outro";

export type ReportErroStatus = "aberto" | "em_analise" | "resolvido";

export interface ReportErro {
  id: string;
  user_id: string;
  empresa_id: string | null;
  extrato_id: string | null;
  categoria: ReportErroCategoria;
  titulo: string;
  descricao: string;
  status: ReportErroStatus;
  resposta: string | null;
  created_at: string;
  updated_at: string;
}
