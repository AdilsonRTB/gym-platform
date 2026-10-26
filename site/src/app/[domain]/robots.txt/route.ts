import { getSite } from "@/lib/api";

// Gerado por domínio no pedido (os dados da API ficam na cache de fetch).
export const dynamic = "force-dynamic";

/** robots.txt por domínio: bloqueia tudo enquanto o ginásio não estiver ativo ou com indexação desligada. */
export async function GET(_: Request, ctx: RouteContext<"/[domain]/robots.txt">) {
  const domain = decodeURIComponent((await ctx.params).domain);
  const site = await getSite(domain);
  const corpo =
    site && site.seo.indexar
      ? `User-agent: *\nAllow: /\nDisallow: /aderir\nDisallow: /gestao\nDisallow: /app\nDisallow: /preview/\nDisallow: /api/\n\nSitemap: ${site.url}/sitemap.xml\n`
      : "User-agent: *\nDisallow: /\n";
  return new Response(corpo, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
}
