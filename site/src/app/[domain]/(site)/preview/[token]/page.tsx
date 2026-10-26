import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Blocks } from "@/components/blocks/Blocks";
import { getPreview } from "@/lib/api";
import { carregarSite } from "@/lib/site";

type Props = { params: Promise<{ domain: string; token: string }> };

export const metadata: Metadata = { title: "Pré-visualização", robots: { index: false, follow: false } };

/** Pré-visualização de uma página em rascunho, aberta a partir do Wagtail (sem cache). */
export default async function Preview({ params }: Props) {
  const { domain: d, token } = await params;
  const { site, domain } = await carregarSite(d);
  const pagina = await getPreview(domain, token);
  if (!pagina) notFound();
  return (
    <>
      <div className="preview-bar" role="status">
        Pré-visualização · {pagina.titulo} · ainda não publicado
      </div>
      <Blocks blocos={pagina.corpo} ctx={{ adesaoOnline: site.adesao_online }} />
    </>
  );
}
