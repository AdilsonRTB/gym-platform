"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type Item = { titulo: string; caminho: string };

export function NavLinks({ itens, onNavigate }: { itens: Item[]; onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <>
      {itens.map((item) => {
        const ativo = item.caminho === "/" ? pathname === "/" : pathname.startsWith(item.caminho.replace(/\/$/, ""));
        return (
          <Link key={item.caminho} href={item.caminho} aria-current={ativo ? "page" : undefined} onClick={onNavigate}>
            {item.titulo}
          </Link>
        );
      })}
    </>
  );
}
