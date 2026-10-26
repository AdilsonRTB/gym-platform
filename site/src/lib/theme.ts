import type { CSSProperties } from "react";

import type { SiteConfig } from "./types";

/** Tema por ginásio: as cores da marca viram variáveis CSS, com contraste garantido. */

function rgb(hex: string): [number, number, number] {
  const h = /^#?([0-9a-f]{6})$/i.exec(hex.trim())?.[1] ?? "000000";
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as [number, number, number];
}

function luminancia(hex: string): number {
  const [r, g, b] = rgb(hex).map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contraste(a: string, b: string): number {
  const [l1, l2] = [luminancia(a), luminancia(b)].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
}

/** Texto legível (preto ou branco) sobre uma cor de fundo. */
export function textoSobre(fundo: string): string {
  return contraste(fundo, "#0a0a0a") >= contraste(fundo, "#ffffff") ? "#0a0a0a" : "#ffffff";
}

/** Usa `cor` sobre `fundo` só se tiver contraste suficiente; senão, `alternativa`. */
function legivel(cor: string, fundo: string, alternativa: string, minimo = 3): string {
  return contraste(cor, fundo) >= minimo ? cor : alternativa;
}

const FONTES: Record<string, string> = {
  inter: "var(--font-inter)",
  manrope: "var(--font-manrope)",
  "space-grotesk": "var(--font-space-grotesk)",
  archivo: "var(--font-archivo)",
  fraunces: "var(--font-fraunces)",
  "dm-sans": "var(--font-dm-sans)",
};

export function temaCss(site: SiteConfig): CSSProperties {
  const { primaria, destaque, fundo } = site.marca.cores;
  // Texto sempre legível sobre o fundo, mesmo com cores de marca extremas.
  const texto = legivel(site.marca.cores.texto, fundo, textoSobre(fundo), 7);
  const escuro = luminancia(fundo) < 0.2;
  // A cor principal é usada em botões; se não se distinguir do fundo, usa-se o texto.
  const botao = legivel(primaria, fundo, texto, 1.6);
  return {
    "--c-bg": fundo,
    "--c-fg": texto,
    "--c-primary": botao,
    "--c-on-primary": textoSobre(botao),
    "--c-accent": destaque,
    "--c-on-accent": textoSobre(destaque),
    // Destaque usado como texto/linhas sobre o fundo (ex.: lima sobre branco → usa o texto).
    "--c-accent-ink": legivel(destaque, fundo, botao, 3),
    "--c-scheme": escuro ? "dark" : "light",
    colorScheme: escuro ? "dark" : "light",
    "--font-heading": FONTES[site.marca.fontes.titulos] ?? FONTES.inter,
    "--font-body": FONTES[site.marca.fontes.texto] ?? FONTES.inter,
  } as CSSProperties;
}
