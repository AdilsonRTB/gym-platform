import type { Metadata } from "next";

import { Schedule } from "@/components/Schedule";
import { getAulas } from "@/lib/api";
import { carregarSite, metadados } from "@/lib/site";

type Props = { params: Promise<{ domain: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { site } = await carregarSite((await params).domain);
  return metadados(site, {
    titulo: "Horário de aulas",
    descricao: `Horário semanal das aulas de grupo do ${site.nome}.`,
    caminho: "/horario",
  });
}

export default async function Horario({ params }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const aulas = await getAulas(site, domain);
  return (
    <>
      <header className="container page-head">
        <p className="eyebrow">Horário</p>
        <h1 className="h1">Aulas da semana</h1>
        <p className="lead">Escolhe o dia e a modalidade. Não precisas de marcação prévia, basta aparecer.</p>
      </header>
      <section className="container">
        <Schedule aulas={aulas} />
      </section>
    </>
  );
}
