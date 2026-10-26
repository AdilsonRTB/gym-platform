/* eslint-disable @next/next/no-img-element -- as imagens já chegam otimizadas (renditions WebP do Wagtail) */
import type { Imagem } from "@/lib/types";

type Props = {
  imagem: Imagem | null | undefined;
  sizes?: string;
  prioridade?: boolean;
  className?: string;
};

/** Imagem responsiva com `srcset` das renditions do CMS e ponto de foco. */
export function Img({ imagem, sizes = "100vw", prioridade = false, className }: Props) {
  if (!imagem) return null;
  const foco = imagem.foco
    ? `${Math.round((imagem.foco.x / imagem.largura) * 100)}% ${Math.round((imagem.foco.y / imagem.altura) * 100)}%`
    : undefined;
  return (
    <img
      src={imagem.url}
      srcSet={imagem.srcset}
      sizes={sizes}
      alt={imagem.alt}
      width={imagem.largura}
      height={imagem.altura}
      loading={prioridade ? "eager" : "lazy"}
      fetchPriority={prioridade ? "high" : undefined}
      decoding="async"
      className={className}
      style={foco ? { objectPosition: foco } : undefined}
    />
  );
}
