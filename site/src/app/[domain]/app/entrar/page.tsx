import { EntrarApp } from "@/components/app/EntrarApp";
import { carregarSite } from "@/lib/site";

export default async function Page({ params }: { params: Promise<{ domain: string }> }) {
  const { site } = await carregarSite((await params).domain);
  return <EntrarApp nome={site.nome} />;
}
