import "server-only";

import type {
  Aula,
  Modalidade,
  ModalidadeResumo,
  Pagina,
  Pergunta,
  Plano,
  Privacidade,
  SiteConfig,
  Testemunho,
  Treinador,
} from "./types";

const API_URL = (process.env.API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const REVALIDATE_FALLBACK = 3600; // o webhook de publicação revalida antes disto

type Opcoes = { tags?: string[]; semCache?: boolean };

/** Pedido à API Django em nome de um ginásio (identificado pelo domínio). */
export async function api<T>(domain: string, path: string, { tags = [], semCache = false }: Opcoes = {}) {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    headers: { "X-Gym-Host": domain, Accept: "application/json" },
    ...(semCache
      ? { cache: "no-store" as const }
      : { cache: "force-cache" as const, next: { tags, revalidate: REVALIDATE_FALLBACK } }),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return (await res.json()) as T;
}

export const getSite = (domain: string) => api<SiteConfig>(domain, "/site/", { tags: [`d:${domain}`] });

/** Todas as funções abaixo recebem o site já carregado, para usar as tags por id do ginásio. */
const t = (site: SiteConfig, ...tipos: string[]) => tipos.map((tipo) => `g:${site.id}:${tipo}`);

export const getPagina = (site: SiteConfig, domain: string, caminho: string) =>
  api<Pagina>(domain, `/paginas/?caminho=${encodeURIComponent(caminho)}`, { tags: t(site, "paginas") });

export const getPaginasLista = (site: SiteConfig, domain: string) =>
  api<{ caminho: string; publicada_em: string | null; indexar: boolean }[]>(domain, "/paginas/lista/", {
    tags: t(site, "paginas"),
  }).then((r) => r ?? []);

export const getModalidades = (site: SiteConfig, domain: string) =>
  api<ModalidadeResumo[]>(domain, "/modalidades/", { tags: t(site, "modalidades") }).then((r) => r ?? []);

export const getModalidade = (site: SiteConfig, domain: string, slug: string) =>
  api<Modalidade>(domain, `/modalidades/${encodeURIComponent(slug)}/`, { tags: t(site, "modalidades", "treinadores") });

export const getTreinadores = (site: SiteConfig, domain: string) =>
  api<Treinador[]>(domain, "/treinadores/", { tags: t(site, "treinadores") }).then((r) => r ?? []);

export const getPlanos = (site: SiteConfig, domain: string) =>
  api<Plano[]>(domain, "/planos/", { tags: t(site, "planos") }).then((r) => r ?? []);

export const getAulas = (site: SiteConfig, domain: string) =>
  api<Aula[]>(domain, "/aulas/", { tags: t(site, "aulas", "modalidades", "treinadores") }).then((r) => r ?? []);

export const getTestemunhos = (site: SiteConfig, domain: string) =>
  api<Testemunho[]>(domain, "/testemunhos/", { tags: t(site, "testemunhos") }).then((r) => r ?? []);

export const getPerguntas = (site: SiteConfig, domain: string) =>
  api<Pergunta[]>(domain, "/perguntas/", { tags: t(site, "faq") }).then((r) => r ?? []);

export const getPrivacidade = (site: SiteConfig, domain: string) =>
  api<Privacidade>(domain, "/privacidade/", { tags: t(site, "site") });

export const getRedirecionamento = (domain: string, caminho: string) =>
  api<{ destino: string; permanente: boolean }>(domain, `/redirecionamento/?caminho=${encodeURIComponent(caminho)}`, {
    semCache: true,
  });

export const getPreview = (domain: string, token: string) =>
  api<Pagina>(domain, `/preview/${encodeURIComponent(token)}/`, { semCache: true });

export const getAdesao = (domain: string, ref: string) =>
  api<{ estado: string; plano: string; valor_cve: number; nome: string; fatura: { numero: string; estado: string } | null }>(
    domain,
    `/adesoes/${encodeURIComponent(ref)}/`,
    { semCache: true },
  );

export { API_URL };
