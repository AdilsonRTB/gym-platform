import type { Metadata } from "next";

import { DataRequestForm } from "@/components/forms/DataRequestForm";
import { getPrivacidade } from "@/lib/api";
import { carregarSite, metadados } from "@/lib/site";

type Props = { params: Promise<{ domain: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { site } = await carregarSite((await params).domain);
  return metadados(site, { titulo: "Política de privacidade", caminho: "/privacidade" });
}

export default async function Privacidade({ params }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const p = await getPrivacidade(site, domain);
  const data = p?.atualizada_em
    ? new Intl.DateTimeFormat("pt-PT", { dateStyle: "long" }).format(new Date(p.atualizada_em))
    : null;

  return (
    <>
      <header className="container page-head">
        <p className="eyebrow">Privacidade</p>
        <h1 className="h1">Política de privacidade</h1>
        <p className="lead">
          Responsável: {p?.responsavel ?? site.nome}
          {data ? ` · Atualizada a ${data}` : ""}
        </p>
      </header>
      <section className="container detail">
        <div
          className="prose"
          dangerouslySetInnerHTML={{
            __html: p?.politica || "<p>A política de privacidade deste ginásio está a ser preparada.</p>",
          }}
        />
        <aside>
          <div className="card">
            <h2 className="h3">Os seus dados</h2>
            <p className="muted small">
              Peça uma cópia ou a eliminação dos seus dados pessoais, nos termos da lei de proteção de dados de Cabo
              Verde.{p?.email ? ` Também pode escrever para ${p.email}.` : ""}
            </p>
            <DataRequestForm />
          </div>
        </aside>
      </section>
    </>
  );
}
