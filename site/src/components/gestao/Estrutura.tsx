"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { pedido } from "@/lib/cliente";
import { iniciais } from "@/lib/format";
import { PAPEL, type Utilizador } from "@/lib/gestaoTypes";

import { Icon } from "../Icon";

const NAV = [
  { href: "/gestao", titulo: "Painel", icone: "haltere" },
  { href: "/gestao/checkin", titulo: "Check-in", icone: "qr" },
  { href: "/gestao/socios", titulo: "Sócios", icone: "pessoas" },
  { href: "/gestao/cobrancas", titulo: "Cobranças", icone: "cartao" },
];

function ativo(pathname: string, href: string) {
  return href === "/gestao" ? pathname === "/gestao" : pathname.startsWith(href);
}


export function Estrutura({
  nomeGinasio,
  utilizador,
  children,
}: {
  nomeGinasio: string;
  utilizador: Utilizador;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const nav = utilizador.papel === "treinador" ? NAV.filter((n) => n.href === "/gestao/checkin") : NAV;

  async function sair() {
    await pedido("gestao", "auth/sair", { corpo: {} });
    router.replace("/gestao/entrar");
    router.refresh();
  }

  return (
    <div className="painel">
      <aside className="painel__lateral">
        <Link href="/gestao" className="brand">
          <span className="brand__mark" aria-hidden="true">
            {nomeGinasio.charAt(0)}
          </span>
          {nomeGinasio}
        </Link>
        <nav className="painel__nav" aria-label="Gestão">
          {nav.map((n) => (
            <Link key={n.href} href={n.href} aria-current={ativo(pathname, n.href) ? "page" : undefined}>
              <Icon name={n.icone} size={18} />
              {n.titulo}
            </Link>
          ))}
          <a href="/" target="_blank" rel="noopener">
            <Icon name="arrow-up-right" size={18} />
            Ver site
          </a>
        </nav>
        <div className="painel__utilizador">
          <span className="avatar">{iniciais(utilizador.nome)}</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <strong>{utilizador.nome}</strong>
            <span className="muted">{PAPEL[utilizador.papel] ?? utilizador.papel}</span>
          </div>
          <button className="icon-btn" onClick={sair} aria-label="Sair" title="Sair">
            <Icon name="sair" size={16} />
          </button>
        </div>
      </aside>

      <header className="painel__topo">
        <Link href="/gestao" className="brand">
          <span className="brand__mark" aria-hidden="true">
            {nomeGinasio.charAt(0)}
          </span>
          {nomeGinasio}
        </Link>
        <button className="icon-btn" onClick={sair} aria-label="Sair" title="Sair">
          <Icon name="sair" size={16} />
        </button>
      </header>

      <main className="painel__main">{children}</main>

      <nav className="painel__tabs" aria-label="Gestão" style={{ gridTemplateColumns: `repeat(${nav.length}, 1fr)` }}>
        {nav.map((n) => (
          <Link key={n.href} href={n.href} aria-current={ativo(pathname, n.href) ? "page" : undefined}>
            <Icon name={n.icone} size={20} />
            {n.titulo}
          </Link>
        ))}
      </nav>
    </div>
  );
}
