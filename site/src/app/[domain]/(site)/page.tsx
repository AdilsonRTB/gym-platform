import type { Metadata } from "next";
import Link from "next/link";

import { Blocks } from "@/components/blocks/Blocks";
import { getPagina } from "@/lib/api";
import { carregarSite, metadados } from "@/lib/site";

type Props = { params: Promise<{ domain: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { site, domain } = await carregarSite((await params).domain);
  const pagina = await getPagina(site, domain, "/");
  return {
    ...metadados(site, {
      descricao: pagina?.seo.descricao,
      imagem: pagina?.seo.imagem,
      caminho: "/",
      indexar: pagina?.seo.indexar,
    }),
    title: { absolute: pagina?.seo.titulo || site.nome },
  };
}

export default async function Home({ params }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const pagina = await getPagina(site, domain, "/");

  if (!pagina || pagina.corpo.length === 0) {
    return (
      <section className="hero hero--centrado">
        <div className="container hero__copy">
          <p className="eyebrow">Brevemente</p>
          <h1 className="display">{site.nome}</h1>
          {site.marca.slogan && <p className="lead">{site.marca.slogan}</p>}
          <div className="hero__actions">
            <Link href="/contactos" className="btn">
              Falar connosco
            </Link>
          </div>
        </div>
      </section>
    );
  }

  return <Blocks blocos={pagina.corpo} ctx={{ adesaoOnline: site.adesao_online }} />;
}
