import type { Metadata } from "next";

import { LeadForm } from "@/components/forms/LeadForm";
import { Icon } from "@/components/Icon";
import { getModalidades } from "@/lib/api";
import { whatsappUrl } from "@/lib/format";
import { carregarSite, metadados } from "@/lib/site";

type Props = {
  params: Promise<{ domain: string }>;
  searchParams: Promise<{ tipo?: string; modalidade?: string; plano?: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { site } = await carregarSite((await params).domain);
  return metadados(site, {
    titulo: "Contactos",
    descricao: `Fale com o ${site.nome} ou marque uma aula experimental grátis.`,
    caminho: "/contactos",
  });
}

export default async function Contactos({ params, searchParams }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const { tipo, modalidade, plano } = await searchParams;
  const modalidades = await getModalidades(site, domain);
  const c = site.contactos;

  return (
    <>
      <header className="container page-head">
        <p className="eyebrow">Contactos</p>
        <h1 className="h1">Vem conhecer-nos.</h1>
        <p className="lead">A primeira aula é grátis. Deixa o teu contacto e ligamos-te para combinar.</p>
      </header>
      <section className="container detail">
        <div className="card">
          <LeadForm
            modalidades={modalidades.map(({ slug, nome }) => ({ slug, nome }))}
            textoConsentimento={site.privacidade.texto_consentimento}
            tipoInicial={tipo === "contacto" || plano ? "contacto" : "aula_experimental"}
            modalidadeInicial={modalidade}
            mensagemInicial={plano ? `Tenho interesse no plano ${plano}.` : undefined}
          />
        </div>
        <aside className="stack" style={{ "--stack": "40px" } as React.CSSProperties}>
          <ul className="contact-list">
            {c.telefone && (
              <li>
                <a href={`tel:${c.telefone.replace(/\s/g, "")}`}>
                  <Icon name="phone" />
                  {c.telefone}
                </a>
              </li>
            )}
            {c.whatsapp && (
              <li>
                <a href={whatsappUrl(c.whatsapp, `Olá ${site.nome}!`)} target="_blank" rel="noopener noreferrer">
                  <Icon name="message" />
                  WhatsApp {c.whatsapp}
                </a>
              </li>
            )}
            {c.email && (
              <li>
                <a href={`mailto:${c.email}`}>
                  <Icon name="mail" />
                  {c.email}
                </a>
              </li>
            )}
            {c.morada && (
              <li>
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${c.morada} ${c.cidade}`)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Icon name="pin" />
                  {c.morada}
                </a>
              </li>
            )}
          </ul>
          {c.horario.length > 0 && (
            <div>
              <h2 className="h3" style={{ marginBottom: 16 }}>
                Horário de funcionamento
              </h2>
              <dl className="hours">
                {c.horario.map((h) => (
                  <div key={h.dias} style={{ display: "contents" }}>
                    <dt>{h.dias}</dt>
                    <dd>{h.horas}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </aside>
      </section>
      {c.mapa_url && (
        <section className="section">
          <div className="container">
            <iframe className="map" src={c.mapa_url} title={`Mapa — ${site.nome}`} loading="lazy" referrerPolicy="no-referrer-when-downgrade" />
          </div>
        </section>
      )}
    </>
  );
}
