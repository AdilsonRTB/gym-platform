import { ImageResponse } from "next/og";

import { getSite } from "@/lib/api";
import { textoSobre } from "@/lib/theme";

export const dynamic = "force-dynamic";

/** Ícone da app gerado com a inicial e a cor de destaque da marca (quando não há favicon). */
export async function GET(_: Request, ctx: RouteContext<"/[domain]/app/icone">) {
  const site = await getSite(decodeURIComponent((await ctx.params).domain));
  const fundo = site?.marca.cores.destaque ?? "#111111";
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: fundo,
          color: textoSobre(fundo),
          fontSize: 300,
          fontWeight: 800,
          letterSpacing: -12,
        }}
      >
        {(site?.nome ?? "G").charAt(0)}
      </div>
    ),
    { width: 512, height: 512 },
  );
}
