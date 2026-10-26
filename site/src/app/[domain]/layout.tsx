import "../globals.css";

import type { Metadata, Viewport } from "next";

import { getSite } from "@/lib/api";
import { fontVariables } from "@/lib/fonts";
import { temaCss } from "@/lib/theme";

type Props = { children: React.ReactNode; params: Promise<{ domain: string }> };

// Os sites são gerados no primeiro pedido de cada domínio e ficam em cache (ISR).
export async function generateStaticParams() {
  return [];
}

export async function generateMetadata({ params }: Omit<Props, "children">): Promise<Metadata> {
  const site = await getSite(decodeURIComponent((await params).domain));
  if (!site) return { title: "Site não encontrado", robots: { index: false } };
  const sufixo = site.seo.titulo_sufixo || site.nome;
  return {
    metadataBase: new URL(site.url),
    title: { default: sufixo, template: `%s · ${sufixo}` },
    description: site.seo.descricao || site.marca.slogan,
    applicationName: site.nome,
    icons: site.marca.favicon ? { icon: site.marca.favicon.url, apple: site.marca.favicon.url } : undefined,
    verification: site.seo.google_verificacao ? { google: site.seo.google_verificacao } : undefined,
  };
}

export async function generateViewport({ params }: Omit<Props, "children">): Promise<Viewport> {
  const site = await getSite(decodeURIComponent((await params).domain));
  return { themeColor: site?.marca.cores.fundo ?? "#ffffff", width: "device-width", initialScale: 1 };
}

/** Layout raiz de cada ginásio: tema (cores e fontes da marca). Site, painel e app têm layouts próprios. */
export default async function RootLayout({ children, params }: Props) {
  const site = await getSite(decodeURIComponent((await params).domain));

  if (!site) {
    return (
      <html lang="pt" className={fontVariables}>
        <body>
          <main className="container not-found">
            <p className="display">404</p>
            <h1 className="h2">Este site não existe.</h1>
            <p className="lead">Verifique o endereço ou contacte o ginásio.</p>
          </main>
        </body>
      </html>
    );
  }

  return (
    <html lang="pt" data-modelo={site.marca.modelo} style={temaCss(site)} className={fontVariables}>
      <body>{children}</body>
    </html>
  );
}
