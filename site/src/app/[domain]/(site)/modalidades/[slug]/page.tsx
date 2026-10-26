import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CoachCard } from "@/components/Content";
import { Icon } from "@/components/Icon";
import { Img } from "@/components/Img";
import { getAulas, getModalidade } from "@/lib/api";
import { DIAS, NIVEL } from "@/lib/format";
import { carregarSite, metadados } from "@/lib/site";

type Props = { params: Promise<{ domain: string; slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { domain: d, slug } = await params;
  const { site, domain } = await carregarSite(d);
  const m = await getModalidade(site, domain, slug);
  if (!m) return {};
  return metadados(site, { titulo: m.nome, descricao: m.resumo, imagem: m.imagem, caminho: `/modalidades/${slug}` });
}

export default async function ModalidadeDetalhe({ params }: Props) {
  const { domain: d, slug } = await params;
  const { site, domain } = await carregarSite(d);
  const [m, aulas] = await Promise.all([getModalidade(site, domain, slug), getAulas(site, domain)]);
  if (!m) notFound();
  const horario = aulas.filter((a) => a.modalidade.slug === m.slug);

  return (
    <>
      <header className="container page-head">
        <nav className="breadcrumb" aria-label="Caminho">
          <Link href="/modalidades">Modalidades</Link>
          <span aria-hidden="true">/</span>
          <span>{m.nome}</span>
        </nav>
        <h1 className="h1">{m.nome}</h1>
        {m.resumo && <p className="lead">{m.resumo}</p>}
      </header>

      {m.imagem && (
        <div className="container">
          <div className="media" style={{ aspectRatio: "21 / 9" }}>
            <Img imagem={m.imagem} prioridade sizes="(min-width: 1264px) 1200px, 100vw" />
          </div>
        </div>
      )}

      <section className="section">
        <div className="container detail">
          <div className="stack" style={{ "--stack": "56px" } as React.CSSProperties}>
            <div className="prose" dangerouslySetInnerHTML={{ __html: m.descricao }} />
            {horario.length > 0 && (
              <div>
                <h2 className="h3" style={{ marginBottom: 16 }}>
                  Quando acontece
                </h2>
                <ul className="schedule">
                  {horario.map((a) => (
                    <li key={a.id} className="slot">
                      <span className="slot__hora">{a.hora_inicio}</span>
                      <div>
                        <div className="slot__nome">{DIAS[a.dia_semana]}</div>
                        <div className="slot__info">
                          {a.treinador && <span>{a.treinador.nome}</span>}
                          {a.sala && <span>{a.sala}</span>}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          <aside>
            <div className="card">
              <dl className="facts">
                <div>
                  <dt>Nível</dt>
                  <dd>{NIVEL[m.nivel]}</dd>
                </div>
                <div>
                  <dt>Duração</dt>
                  <dd>{m.duracao_min} min</dd>
                </div>
                <div>
                  <dt>Aulas por semana</dt>
                  <dd>{horario.length}</dd>
                </div>
              </dl>
              <Link href={`/contactos?tipo=aula_experimental&modalidade=${m.slug}`} className="btn btn--block">
                Experimentar grátis <Icon name="arrow-right" size={16} />
              </Link>
            </div>
          </aside>
        </div>
      </section>

      {m.treinadores.length > 0 && (
        <section className="section">
          <div className="container">
            <h2 className="h2" style={{ marginBottom: 40 }}>
              Quem dá esta aula
            </h2>
            <div className="grid grid--4">
              {m.treinadores.map((t) => (
                <CoachCard key={t.id} t={t} />
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
}
