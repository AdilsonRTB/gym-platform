"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon } from "./Icon";
import { NavLinks } from "./NavLinks";

type Props = { itens: { titulo: string; caminho: string }[]; cta: { texto: string; href: string } };

export function MobileNav({ itens, cta }: Props) {
  const [aberto, setAberto] = useState(false);
  // Bloqueia o scroll da página enquanto o menu está aberto (os links fecham-no ao navegar).
  useEffect(() => {
    document.body.style.overflow = aberto ? "hidden" : "";
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setAberto(false);
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
    };
  }, [aberto]);

  return (
    <>
      <button
        type="button"
        className="menu-toggle"
        aria-expanded={aberto}
        aria-controls="menu-movel"
        aria-label={aberto ? "Fechar menu" : "Abrir menu"}
        onClick={() => setAberto((v) => !v)}
      >
        <Icon name={aberto ? "x" : "menu"} />
      </button>
      {aberto && (
        <nav id="menu-movel" className="mobile-nav" aria-label="Menu">
          <NavLinks itens={itens} onNavigate={() => setAberto(false)} />
          <Link href={cta.href} className="btn btn--block" onClick={() => setAberto(false)}>
            {cta.texto}
            <Icon name="arrow-right" size={16} />
          </Link>
        </nav>
      )}
    </>
  );
}
