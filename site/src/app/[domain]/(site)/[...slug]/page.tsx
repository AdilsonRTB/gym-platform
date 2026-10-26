import type { Metadata } from "next";
import { notFound, permanentRedirect, redirect } from "next/navigation";

import { Blocks } from "@/components/blocks/Blocks";
import { getPagina, getRedirecionamento } from "@/lib/api";
import { carregarSite, metadados } from "@/lib/site";

type Props = { params: Promise<{ domain: string; slug: string[] }> };

const caminhoDe = (slug: string[]) => `/${slug.map(decodeURIComponent).join("/")}/`;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { domain: d, slug } = await params;
  const { site, domain } = await carregarSite(d);
  const pagina = await getPagina(site, domain, caminhoDe(slug));
  if (!pagina) return {};
  return metadados(site, {
    titulo: pagina.seo.titulo,
    descricao: pagina.seo.descricao,
    imagem: pagina.seo.imagem,
    caminho: pagina.caminho,
    indexar: pagina.seo.indexar,
  });
}

/** Páginas criadas no CMS (ex.: /sobre, /instalacoes) e redirecionamentos configurados no Admin. */
export default async function PaginaCms({ params }: Props) {
  const { domain: d, slug } = await params;
  const { site, domain } = await carregarSite(d);
  const caminho = caminhoDe(slug);
  const pagina = await getPagina(site, domain, caminho);

  if (!pagina) {
    const destino = await getRedirecionamento(domain, caminho.replace(/\/$/, ""));
    if (destino) (destino.permanente ? permanentRedirect : redirect)(destino.destino);
    notFound();
  }
  return <Blocks blocos={pagina.corpo} ctx={{ adesaoOnline: site.adesao_online }} />;
}
