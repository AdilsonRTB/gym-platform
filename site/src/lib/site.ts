import "server-only";

import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { cache } from "react";

import { getSite } from "./api";
import type { Imagem, SiteConfig } from "./types";

/** Site do ginásio a partir do parâmetro `[domain]` (deduplicado por pedido). */
export const carregarSite = cache(async (domainParam: string) => {
  const domain = decodeURIComponent(domainParam);
  const site = await getSite(domain);
  if (!site) notFound();
  return { site, domain };
});

type Opcoes = {
  titulo?: string;
  descricao?: string;
  imagem?: Imagem | null;
  caminho: string;
  indexar?: boolean;
};

/** Metadados de SEO por página, com título, partilha e indexação por ginásio. */
export function metadados(site: SiteConfig, { titulo, descricao, imagem, caminho, indexar = true }: Opcoes): Metadata {
  const img = imagem ?? site.seo.imagem;
  const desc = descricao || site.seo.descricao || site.marca.slogan;
  const index = site.seo.indexar && indexar;
  return {
    title: titulo,
    description: desc,
    alternates: { canonical: caminho },
    robots: index ? { index: true, follow: true } : { index: false, follow: false },
    openGraph: {
      type: "website",
      siteName: site.nome,
      locale: "pt_CV",
      title: titulo ?? site.nome,
      description: desc,
      url: caminho,
      images: img ? [{ url: img.url, width: img.largura, height: img.altura, alt: img.alt }] : undefined,
    },
    twitter: { card: img ? "summary_large_image" : "summary" },
  };
}
