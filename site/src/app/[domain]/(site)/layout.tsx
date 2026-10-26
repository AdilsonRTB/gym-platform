import Script from "next/script";

import { CookieBanner } from "@/components/CookieBanner";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { Icon } from "@/components/Icon";
import { GymJsonLd } from "@/components/JsonLd";
import { whatsappUrl } from "@/lib/format";
import { carregarSite } from "@/lib/site";

type Props = { children: React.ReactNode; params: Promise<{ domain: string }> };

/** Site público: cabeçalho, rodapé, WhatsApp, analítica e dados estruturados. */
export default async function SiteLayout({ children, params }: Props) {
  const { site } = await carregarSite((await params).domain);
  return (
    <>
      <a className="skip-link" href="#conteudo">
        Saltar para o conteúdo
      </a>
      <Header site={site} />
      <main id="conteudo">{children}</main>
      <Footer site={site} />
      {site.contactos.whatsapp && (
        <a
          className="whatsapp-fab"
          href={whatsappUrl(site.contactos.whatsapp, `Olá ${site.nome}!`)}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Falar connosco no WhatsApp"
        >
          <Icon name="message" size={26} />
        </a>
      )}
      {site.seo.plausible_dominio && (
        <Script defer data-domain={site.seo.plausible_dominio} src="https://plausible.io/js/script.js" />
      )}
      {site.seo.ga4_id && <CookieBanner ga4Id={site.seo.ga4_id} />}
      <GymJsonLd site={site} />
    </>
  );
}
