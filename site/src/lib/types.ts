export type Imagem = {
  id: number;
  alt: string;
  url: string;
  largura: number;
  altura: number;
  srcset: string;
  foco: { x: number; y: number } | null;
};

export type Modelo = "essencial" | "energia" | "atelier";

export type SiteConfig = {
  id: number;
  nome: string;
  slug: string;
  dominio: string;
  url: string;
  moeda: string;
  marca: {
    modelo: Modelo;
    slogan: string;
    logotipo: Imagem | null;
    logotipo_claro: Imagem | null;
    favicon: Imagem | null;
    cores: { primaria: string; destaque: string; fundo: string; texto: string };
    fontes: { titulos: string; texto: string };
  };
  contactos: {
    telefone: string;
    whatsapp: string;
    email: string;
    morada: string;
    cidade: string;
    mapa_url: string;
    horario: { dias: string; horas: string }[];
  };
  redes: Partial<Record<"instagram" | "facebook" | "tiktok" | "youtube", string>>;
  seo: {
    titulo_sufixo: string;
    descricao: string;
    imagem: Imagem | null;
    indexar: boolean;
    google_verificacao: string;
    plausible_dominio: string;
    ga4_id: string;
  };
  privacidade: { texto_consentimento: string };
  menu: { titulo: string; caminho: string }[];
  adesao_online: boolean;
};

export type Bloco = { type: string; id: string; value: any }; // eslint-disable-line @typescript-eslint/no-explicit-any

export type Pagina = {
  id: number;
  tipo: string;
  titulo: string;
  caminho: string;
  seo: { titulo: string; descricao: string; imagem: Imagem | null; indexar: boolean };
  corpo: Bloco[];
  publicada_em: string | null;
};

export type ModalidadeResumo = {
  id: number;
  slug: string;
  nome: string;
  resumo: string;
  imagem: Imagem | null;
  nivel: "todos" | "iniciante" | "intermedio" | "avancado";
  duracao_min: number;
};

export type Treinador = {
  id: number;
  slug: string;
  nome: string;
  cargo: string;
  foto: Imagem | null;
  especialidades: string[];
  biografia: string;
  instagram: string;
  modalidades: string[];
};

export type Modalidade = ModalidadeResumo & { descricao: string; treinadores: Treinador[] };

export type Plano = {
  id: number;
  nome: string;
  descricao: string;
  preco_cve: number;
  periodicidade: "avulso" | "semanal" | "mensal" | "trimestral" | "semestral" | "anual";
  taxa_inscricao_cve: number;
  beneficios: string[];
  destaque: boolean;
  adesao_online: boolean;
};

export type Aula = {
  id: number;
  dia_semana: number;
  hora_inicio: string;
  hora_fim: string;
  sala: string;
  lotacao: number | null;
  modalidade: { slug: string; nome: string };
  treinador: { slug: string; nome: string } | null;
};

export type Testemunho = { id: number; texto: string; autor: string; detalhe: string; foto: Imagem | null };
export type Pergunta = { id: number; pergunta: string; resposta: string };

export type Privacidade = {
  responsavel: string;
  email: string;
  politica: string;
  atualizada_em: string | null;
  texto_consentimento: string;
};
