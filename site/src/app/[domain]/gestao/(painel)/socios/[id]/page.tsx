import { FichaSocio } from "@/components/gestao/FichaSocio";
import { getPlanos } from "@/lib/api";
import { carregarSite } from "@/lib/site";

export const metadata = { title: "Sócio" };

type Props = { params: Promise<{ domain: string; id: string }> };

export default async function Page({ params }: Props) {
  const { domain: d, id } = await params;
  const { site, domain } = await carregarSite(d);
  const planos = await getPlanos(site, domain);
  return <FichaSocio id={Number(id)} planos={planos} />;
}
