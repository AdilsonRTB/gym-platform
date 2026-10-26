import Link from "next/link";

import { whatsappUrl } from "@/lib/format";
import type { SiteConfig } from "@/lib/types";

import { Marca, navegacao } from "./Header";
import { Icon } from "./Icon";

export function Footer({ site }: { site: SiteConfig }) {
  const { contactos: c, redes } = site;
  const ano = new Date().getFullYear();
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer__grid">
          <div>
            <Marca site={site} />
            {site.marca.slogan && <p className="footer__slogan">{site.marca.slogan}</p>}
            {Object.keys(redes).length > 0 && (
              <div className="socials">
                {Object.entries(redes).map(([rede, url]) => (
                  <a key={rede} href={url} target="_blank" rel="noopener noreferrer" aria-label={rede}>
                    <Icon name={rede} size={18} />
                  </a>
                ))}
              </div>
            )}
          </div>
          <div>
            <h2>Explorar</h2>
            <ul>
              {navegacao(site).map((item) => (
                <li key={item.caminho}>
                  <Link href={item.caminho}>{item.titulo}</Link>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h2>Contactos</h2>
            <ul>
              {c.morada && <li>{c.morada}</li>}
              {c.telefone && (
                <li>
                  <a href={`tel:${c.telefone.replace(/\s/g, "")}`}>{c.telefone}</a>
                </li>
              )}
              {c.whatsapp && (
                <li>
                  <a href={whatsappUrl(c.whatsapp)} target="_blank" rel="noopener noreferrer">
                    WhatsApp
                  </a>
                </li>
              )}
              {c.email && (
                <li>
                  <a href={`mailto:${c.email}`}>{c.email}</a>
                </li>
              )}
            </ul>
          </div>
          {c.horario.length > 0 && (
            <div>
              <h2>Horário</h2>
              <dl className="hours">
                {c.horario.map((h) => (
                  <HorarioLinha key={h.dias} {...h} />
                ))}
              </dl>
            </div>
          )}
        </div>
        <div className="footer__bottom">
          <span>
            © {ano} {site.nome}
          </span>
          <nav aria-label="Legal">
            <Link href="/privacidade">Privacidade</Link>
            <Link href="/contactos">Contactos</Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}

function HorarioLinha({ dias, horas }: { dias: string; horas: string }) {
  return (
    <>
      <dt>{dias}</dt>
      <dd>{horas}</dd>
    </>
  );
}
