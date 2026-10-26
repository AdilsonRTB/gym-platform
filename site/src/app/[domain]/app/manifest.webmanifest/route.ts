import { getSite } from "@/lib/api";

export const dynamic = "force-dynamic";

/** Manifesto PWA por ginásio: nome, cores e ícone da marca. */
export async function GET(_: Request, ctx: RouteContext<"/[domain]/app/manifest.webmanifest">) {
  const site = await getSite(decodeURIComponent((await ctx.params).domain));
  if (!site) return new Response("Not found", { status: 404 });
  const icone = site.marca.favicon?.url ?? "/app/icone";
  return Response.json(
    {
      name: site.nome,
      short_name: site.nome.length > 12 ? site.nome.split(" ")[0] : site.nome,
      description: `App de sócio do ${site.nome}`,
      start_url: "/app",
      scope: "/app",
      display: "standalone",
      background_color: site.marca.cores.fundo,
      theme_color: site.marca.cores.fundo,
      lang: "pt",
      icons: [
        { src: icone, sizes: "512x512", type: site.marca.favicon ? "image/webp" : "image/png", purpose: "any" },
        { src: "/app/icone", sizes: "512x512", type: "image/png", purpose: "maskable" },
      ],
    },
    { headers: { "Content-Type": "application/manifest+json" } },
  );
}
