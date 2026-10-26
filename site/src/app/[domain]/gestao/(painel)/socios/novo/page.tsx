import { NovoSocio } from "@/components/gestao/NovoSocio";
import { getPlanos } from "@/lib/api";
import { carregarSite } from "@/lib/site";

export const metadata = { title: "Novo sócio" };

export default async function Page({ params }: { params: Promise<{ domain: string }> }) {
  const { site, domain } = await carregarSite((await params).domain);
  const planos = await getPlanos(site, domain);
  return <NovoSocio planos={planos} />;
}
