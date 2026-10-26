import type { Metadata } from "next";

import { ClassCard } from "@/components/Content";
import { getModalidades } from "@/lib/api";
import { carregarSite, metadados } from "@/lib/site";

type Props = { params: Promise<{ domain: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { site } = await carregarSite((await params).domain);
  return metadados(site, {
    titulo: "Modalidades",
    descricao: `Todas as aulas e modalidades do ${site.nome}.`,
    caminho: "/modalidades",
  });
}

export default async function Modalidades({ params }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const modalidades = await getModalidades(site, domain);
  return (
    <>
      <header className="container page-head">
        <p className="eyebrow">Modalidades</p>
        <h1 className="h1">Encontra o treino certo para ti.</h1>
        <p className="lead">
          {modalidades.length} modalidades para todos os níveis, orientadas por treinadores certificados.
        </p>
      </header>
      <section className="container">
        {modalidades.length ? (
          <div className="grid grid--3" style={{ "--grid-gap": "40px 24px" } as React.CSSProperties}>
            {modalidades.map((m, i) => (
              <ClassCard key={m.id} m={m} prioridade={i < 3} />
            ))}
          </div>
        ) : (
          <div className="empty">As modalidades vão ser anunciadas em breve.</div>
        )}
      </section>
    </>
  );
}
