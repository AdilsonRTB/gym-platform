import Link from "next/link";

import { formatarCve, iniciais, NIVEL, PERIODICIDADE } from "@/lib/format";
import type { ModalidadeResumo, Pergunta, Plano, Testemunho, Treinador } from "@/lib/types";

import { Icon } from "./Icon";
import { Img } from "./Img";

export function SectionHead({
  eyebrow,
  titulo,
  subtitulo,
  acao,
}: {
  eyebrow?: string;
  titulo?: string;
  subtitulo?: string;
  acao?: { texto: string; href: string };
}) {
  if (!titulo && !subtitulo && !eyebrow) return null;
  return (
    <div className="section-head">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        {titulo && <h2 className="h2">{titulo}</h2>}
        {subtitulo && (
          <p className="lead" style={{ marginTop: 16 }}>
            {subtitulo}
          </p>
        )}
      </div>
      {acao && (
        <Link href={acao.href} className="link-arrow">
          {acao.texto} <Icon name="arrow-right" size={16} />
        </Link>
      )}
    </div>
  );
}

export function ClassCard({ m, prioridade = false }: { m: ModalidadeResumo; prioridade?: boolean }) {
  return (
    <Link href={`/modalidades/${m.slug}`} className="class-card">
      <div className="media">
        <Img imagem={m.imagem} sizes="(min-width: 960px) 380px, (min-width: 640px) 50vw, 100vw" prioridade={prioridade} />
      </div>
      <div className="class-card__meta">
        <span className="badge">{NIVEL[m.nivel]}</span>
        <span className="badge">{m.duracao_min} min</span>
      </div>
      <div className="class-card__title">
        <h3 className="h3">{m.nome}</h3>
        <Icon name="arrow-up-right" />
      </div>
      {m.resumo && <p>{m.resumo}</p>}
    </Link>
  );
}

export function PlanCard({ plano, adesaoOnline }: { plano: Plano; adesaoOnline: boolean }) {
  const online = adesaoOnline && plano.adesao_online;
  const href = online ? `/aderir?plano=${plano.id}` : `/contactos?plano=${encodeURIComponent(plano.nome)}`;
  return (
    <article className={`plan${plano.destaque ? " plan--destaque" : ""}`}>
      <div className="plan__head">
        <h3 className="plan__nome">{plano.nome}</h3>
        {plano.destaque && <span className="badge badge--accent">Mais escolhido</span>}
      </div>
      <div>
        <div className="plan__preco">
          <span className="plan__valor">{formatarCve(plano.preco_cve)}</span>
          <span className="plan__moeda">CVE</span>
          <span className="plan__periodo">{PERIODICIDADE[plano.periodicidade]}</span>
        </div>
        {plano.descricao && (
          <p className="plan__desc" style={{ marginTop: 12 }}>
            {plano.descricao}
          </p>
        )}
      </div>
      {plano.beneficios.length > 0 && (
        <ul className="plan__lista">
          {plano.beneficios.map((b) => (
            <li key={b}>
              <Icon name="check" size={16} />
              {b}
            </li>
          ))}
        </ul>
      )}
      <div>
        <Link href={href} className={`btn btn--block${plano.destaque ? "" : " btn--ghost"}`}>
          {online ? "Aderir agora" : "Quero este plano"}
        </Link>
        {plano.taxa_inscricao_cve > 0 && (
          <p className="plan__taxa small" style={{ marginTop: 12, textAlign: "center" }}>
            + {formatarCve(plano.taxa_inscricao_cve)} CVE de inscrição
          </p>
        )}
      </div>
    </article>
  );
}

export function PlanGrid({ planos, adesaoOnline }: { planos: Plano[]; adesaoOnline: boolean }) {
  return (
    <div className="plans">
      {planos.map((p) => (
        <PlanCard key={p.id} plano={p} adesaoOnline={adesaoOnline} />
      ))}
    </div>
  );
}

export function CoachCard({ t }: { t: Treinador }) {
  return (
    <article className="coach">
      <div className="media">
        {t.foto ? (
          <Img imagem={t.foto} sizes="(min-width: 960px) 280px, 50vw" />
        ) : (
          <div className="coach__monograma" aria-hidden="true">
            {iniciais(t.nome)}
          </div>
        )}
      </div>
      <div>
        <h3 className="h3">{t.nome}</h3>
        {t.cargo && <p className="coach__cargo">{t.cargo}</p>}
      </div>
      {t.especialidades.length > 0 && (
        <div className="coach__tags">
          {t.especialidades.map((e) => (
            <span key={e} className="badge">
              {e}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}

export function Quotes({ itens }: { itens: Testemunho[] }) {
  return (
    <div className="quotes">
      {itens.map((q) => (
        <figure key={q.id} className="quote">
          <blockquote>“{q.texto}”</blockquote>
          <figcaption>
            <span className="quote__avatar" aria-hidden="true">
              {q.foto ? <Img imagem={q.foto} sizes="40px" /> : iniciais(q.autor)}
            </span>
            <span>
              <strong>{q.autor}</strong>
              {q.detalhe && <span className="quote__detalhe">{q.detalhe}</span>}
            </span>
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

export function Faq({ itens }: { itens: Pergunta[] }) {
  return (
    <div className="faq">
      {itens.map((p, i) => (
        <details key={p.id} open={i === 0}>
          <summary>
            {p.pergunta}
            <Icon name="plus" />
          </summary>
          <p>{p.resposta}</p>
        </details>
      ))}
    </div>
  );
}
