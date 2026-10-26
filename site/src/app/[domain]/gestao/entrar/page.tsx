import { redirect } from "next/navigation";

import { LoginEquipa } from "@/components/gestao/LoginEquipa";
import { carregarSite } from "@/lib/site";
import { apiPrivada } from "@/lib/sessao";

type Props = { params: Promise<{ domain: string }> };

export const metadata = { title: "Entrar" };

export default async function Entrar({ params }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const { status } = await apiPrivada("gestao", domain, "/auth/eu/");
  if (status === 200) redirect("/gestao");
  return <LoginEquipa nome={site.nome} />;
}
