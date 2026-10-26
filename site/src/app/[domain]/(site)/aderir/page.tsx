import type { Metadata } from "next";
import Link from "next/link";

import { JoinFlow } from "@/components/forms/JoinFlow";
import { getPlanos } from "@/lib/api";
import { carregarSite, metadados } from "@/lib/site";

type Props = { params: Promise<{ domain: string }>; searchParams: Promise<{ plano?: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { site } = await carregarSite((await params).domain);
  return metadados(site, { titulo: "Aderir", caminho: "/aderir", indexar: false });
}

export default async function Aderir({ params, searchParams }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const { plano } = await searchParams;
  const planos = (await getPlanos(site, domain)).filter((p) => p.adesao_online);

  return (
    <>
      <header className="container page-head">
        <ol className="steps" aria-label="Passos">
          <li aria-current="step">
            <span className="steps__n">1</span>Plano e dados
          </li>
          <li>
            <span className="steps__n">2</span>Pagamento
          </li>
          <li>
            <span className="steps__n">3</span>Bem-vindo
          </li>
        </ol>
        <h1 className="h1">Torna-te sócio.</h1>
        <p className="lead">Escolhe o plano, preenche os teus dados e paga com cartão Vinti4. A fatura chega por email.</p>
      </header>
      <section className="container">
        {site.adesao_online && planos.length > 0 ? (
          <JoinFlow
            planos={planos}
            planoInicial={plano ? Number(plano) : undefined}
            textoConsentimento={site.privacidade.texto_consentimento}
          />
        ) : (
          <div className="empty">
            <p style={{ marginTop: 0 }}>A adesão online ainda não está disponível. Fale connosco para se inscrever.</p>
            <Link href="/contactos" className="btn">
              Contactar o ginásio
            </Link>
          </div>
        )}
      </section>
    </>
  );
}
