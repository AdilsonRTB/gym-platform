import { redirect } from "next/navigation";

import { Estrutura } from "@/components/gestao/Estrutura";
import type { Utilizador } from "@/lib/gestaoTypes";
import { carregarSite } from "@/lib/site";
import { apiPrivada } from "@/lib/sessao";

type Props = { children: React.ReactNode; params: Promise<{ domain: string }> };

/** Área privada: só a equipa do ginásio (a API volta a validar o token em cada pedido). */
export default async function PainelLayout({ children, params }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const { status, dados } = await apiPrivada<Utilizador>("gestao", domain, "/auth/eu/");
  if (status !== 200 || !dados) redirect("/gestao/entrar");
  return (
    <Estrutura nomeGinasio={site.nome} utilizador={dados}>
      {children}
    </Estrutura>
  );
}
