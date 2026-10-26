import "../gestao/painel.css";

import type { Metadata } from "next";

import { RegistarSW } from "@/components/RegistarSW";
import { carregarSite } from "@/lib/site";

// Dados privados (sessão): nunca em cache partilhada.
export const dynamic = "force-dynamic";

type Props = { children: React.ReactNode; params: Promise<{ domain: string }> };

export async function generateMetadata({ params }: Omit<Props, "children">): Promise<Metadata> {
  const { site } = await carregarSite((await params).domain);
  return {
    title: { absolute: site.nome },
    manifest: "/app/manifest.webmanifest",
    robots: { index: false, follow: false },
    appleWebApp: { capable: true, title: site.nome, statusBarStyle: "default" },
    icons: { apple: "/app/icone" },
  };
}

/** App do sócio: uma app web instalável com a marca de cada ginásio. */
export default function AppLayout({ children }: Props) {
  return (
    <>
      {children}
      <RegistarSW />
    </>
  );
}
