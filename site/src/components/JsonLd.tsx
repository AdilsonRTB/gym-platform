import type { SiteConfig } from "@/lib/types";

/** Dados estruturados (schema.org) para o Google mostrar morada, telefone e horário. */
export function GymJsonLd({ site }: { site: SiteConfig }) {
  const c = site.contactos;
  const dados = {
    "@context": "https://schema.org",
    "@type": "ExerciseGym",
    name: site.nome,
    url: site.url,
    description: site.seo.descricao || site.marca.slogan,
    image: site.seo.imagem?.url,
    logo: site.marca.logotipo?.url,
    telephone: c.telefone || undefined,
    email: c.email || undefined,
    priceRange: "CVE",
    currenciesAccepted: "CVE",
    address: c.morada
      ? { "@type": "PostalAddress", streetAddress: c.morada, addressLocality: c.cidade, addressCountry: "CV" }
      : undefined,
    sameAs: Object.values(site.redes),
  };
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(dados).replace(/</g, "\\u003c") }}
    />
  );
}
