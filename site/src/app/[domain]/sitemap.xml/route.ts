import { getModalidades, getPaginasLista, getSite } from "@/lib/api";

// Gerado por domínio no pedido (os dados da API ficam na cache de fetch).
export const dynamic = "force-dynamic";

const FIXAS = ["/modalidades", "/horario", "/planos", "/equipa", "/contactos", "/privacidade"];

/** Sitemap por domínio: páginas do CMS, páginas fixas e modalidades. */
export async function GET(_: Request, ctx: RouteContext<"/[domain]/sitemap.xml">) {
  const domain = decodeURIComponent((await ctx.params).domain);
  const site = await getSite(domain);
  if (!site) return new Response("Not found", { status: 404 });
  const [paginas, modalidades] = await Promise.all([getPaginasLista(site, domain), getModalidades(site, domain)]);

  const urls = [
    ...paginas.filter((p) => p.indexar).map((p) => ({ loc: p.caminho, lastmod: p.publicada_em })),
    ...FIXAS.map((loc) => ({ loc, lastmod: null })),
    ...modalidades.map((m) => ({ loc: `/modalidades/${m.slug}`, lastmod: null })),
  ];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls
  .map(
    (u) =>
      `  <url><loc>${site.url}${u.loc}</loc>${u.lastmod ? `<lastmod>${u.lastmod.slice(0, 10)}</lastmod>` : ""}</url>`,
  )
  .join("\n")}
</urlset>`;
  return new Response(xml, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
}
