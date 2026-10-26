export type Assinatura = {
  id: number;
  plano: string;
  plano_id: number;
  periodicidade: string;
  preco_cve: number;
  data_inicio: string;
  data_fim: string;
  estado: "ativa" | "cancelada";
  valida: boolean;
  dias_restantes: number;
};

export type Cobranca = {
  id: number;
  uuid: string;
  descricao: string;
  periodo_inicio: string;
  periodo_fim: string;
  valor_cve: number;
  vencimento: string;
  estado: "pendente" | "paga" | "anulada";
  atrasada: boolean;
  paga_em: string | null;
  fatura: { numero: string; estado: string } | null;
  metodo: string | null;
  socio?: { id: number; numero: number; nome: string; telefone: string };
};

export type CheckIn = {
  id: number;
  momento: string;
  permitido: boolean;
  motivo: string;
  origem: string;
  offline: boolean;
  socio: { id: number; numero: number; nome: string } | null;
};

export type SocioResumo = {
  id: number;
  numero: number;
  nome: string;
  email: string;
  telefone: string;
  estado: "ativo" | "suspenso" | "inativo";
  assinatura: Assinatura | null;
  em_atraso: boolean;
  criado_em: string;
};

export type Socio = SocioResumo & {
  codigo: string;
  nif: string;
  data_nascimento: string | null;
  morada: string;
  contacto_emergencia: string;
  lembretes: boolean;
  notas: string;
  cobrancas: Cobranca[];
  checkins: CheckIn[];
  historico_assinaturas: Assinatura[];
};

export type Pagina<T> = { count: number; next: string | null; previous: string | null; results: T[] };

export type Utilizador = { nome: string; papel: string };

export type Resumo = {
  socios_ativos: number;
  socios_total: number;
  checkins_hoje: number;
  checkins_negados_hoje: number;
  em_atraso: { n: number; total: number | null };
  receita_mes: number;
  checkins_por_hora: number[];
  ultimos_checkins: CheckIn[];
  a_vencer: Cobranca[];
};

export const PAPEL: Record<string, string> = {
  dono: "Dono",
  gestor: "Gestor",
  rececionista: "Receção",
  treinador: "Treinador",
  plataforma: "Plataforma",
};
