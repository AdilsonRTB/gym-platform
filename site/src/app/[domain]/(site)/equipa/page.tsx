import type { Metadata } from "next";

import { CoachCard } from "@/components/Content";
import { getTreinadores } from "@/lib/api";
import { carregarSite, metadados } from "@/lib/site";

type Props = { params: Promise<{ domain: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { site } = await carregarSite((await params).domain);
  return metadados(site, { titulo: "Equipa", descricao: `Os treinadores do ${site.nome}.`, caminho: "/equipa" });
}

export default async function Equipa({ params }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const treinadores = await getTreinadores(site, domain);
  return (
    <>
      <header className="container page-head">
        <p className="eyebrow">Equipa</p>
        <h1 className="h1">Pessoas que treinam contigo.</h1>
        <p className="lead">Treinadores certificados, presentes na sala e nas aulas, para te ajudar a evoluir com segurança.</p>
      </header>
      <section className="container">
        <div className="grid grid--4" style={{ "--grid-gap": "48px 24px" } as React.CSSProperties}>
          {treinadores.map((t) => (
            <div key={t.id} className="stack" style={{ "--stack": "12px" } as React.CSSProperties}>
              <CoachCard t={t} />
              {t.biografia && <p className="muted small" style={{ margin: 0 }}>{t.biografia}</p>}
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
