import type { Metadata } from "next";

import { Faq, PlanGrid } from "@/components/Content";
import { getPerguntas, getPlanos } from "@/lib/api";
import { carregarSite, metadados } from "@/lib/site";

type Props = { params: Promise<{ domain: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { site } = await carregarSite((await params).domain);
  return metadados(site, {
    titulo: "Planos e preços",
    descricao: `Planos do ${site.nome} em escudos (CVE), com fatura incluída.`,
    caminho: "/planos",
  });
}

export default async function Planos({ params }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const [planos, perguntas] = await Promise.all([getPlanos(site, domain), getPerguntas(site, domain)]);
  return (
    <>
      <header className="container page-head">
        <p className="eyebrow">Planos</p>
        <h1 className="h1">Simples, sem letras pequenas.</h1>
        <p className="lead">
          Preços em escudos, fatura sempre incluída.
          {site.adesao_online ? " Adere online com cartão Vinti4 em menos de dois minutos." : ""}
        </p>
      </header>
      <section className="container">
        {planos.length ? (
          <PlanGrid planos={planos} adesaoOnline={site.adesao_online} />
        ) : (
          <div className="empty">Os planos vão ser publicados em breve.</div>
        )}
      </section>
      {perguntas.length > 0 && (
        <section className="section">
          <div className="container faq-layout">
            <h2 className="h2">Dúvidas frequentes</h2>
            <Faq itens={perguntas} />
          </div>
        </section>
      )}
    </>
  );
}
