import Link from "next/link";

import type { SiteConfig } from "@/lib/types";

import { Icon } from "./Icon";
import { Img } from "./Img";
import { MobileNav } from "./MobileNav";
import { NavLinks } from "./NavLinks";

export function navegacao(site: SiteConfig) {
  return [
    { titulo: "Modalidades", caminho: "/modalidades" },
    { titulo: "Horário", caminho: "/horario" },
    { titulo: "Planos", caminho: "/planos" },
    { titulo: "Equipa", caminho: "/equipa" },
    ...site.menu,
    { titulo: "Contactos", caminho: "/contactos" },
  ];
}

export function Marca({ site }: { site: SiteConfig }) {
  const logo = site.marca.modelo === "energia" ? (site.marca.logotipo_claro ?? site.marca.logotipo) : site.marca.logotipo;
  return (
    <Link href="/" className="brand" aria-label={`${site.nome} — início`}>
      {logo ? (
        <Img imagem={logo} sizes="160px" prioridade />
      ) : (
        <>
          <span className="brand__mark" aria-hidden="true">
            {site.nome.charAt(0)}
          </span>
          <span>{site.nome}</span>
        </>
      )}
    </Link>
  );
}

export function Header({ site }: { site: SiteConfig }) {
  const itens = navegacao(site);
  const cta = site.adesao_online
    ? { texto: "Aderir", href: "/aderir" }
    : { texto: "Aula grátis", href: "/contactos?tipo=aula_experimental" };
  return (
    <header className="header">
      <div className="container header__inner">
        <Marca site={site} />
        <nav className="nav" aria-label="Principal">
          <NavLinks itens={itens} />
        </nav>
        <div className="header__actions">
          <Link href={cta.href} className="btn btn--sm header__cta">
            {cta.texto}
            <Icon name="arrow-right" size={16} />
          </Link>
          <MobileNav itens={itens} cta={cta} />
        </div>
      </div>
    </header>
  );
}
