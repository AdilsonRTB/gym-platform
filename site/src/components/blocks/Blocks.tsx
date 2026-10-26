import type { Bloco } from "@/lib/types";

import { ClassCard, CoachCard, Faq, PlanGrid, Quotes, SectionHead } from "../Content";
import { Icon } from "../Icon";
import { Img } from "../Img";
import { SmartLink } from "../SmartLink";
import { TodaySchedule } from "../TodaySchedule";

/* eslint-disable @typescript-eslint/no-explicit-any -- os valores dos blocos vêm do StreamField */

type Ctx = { adesaoOnline: boolean };
type Link = { texto?: string; link?: string } | null;

const temLink = (l: Link): l is { texto: string; link: string } => Boolean(l?.texto && l?.link);

function Hero({ v, primeiro }: { v: any; primeiro: boolean }) {
  const variante: string = v.imagem ? v.variante : "centrado";
  const Titulo = primeiro ? "h1" : "h2";
  const copy = (
    <div className="hero__copy">
      {v.etiqueta && <p className="eyebrow">{v.etiqueta}</p>}
      <Titulo className="display">{v.titulo}</Titulo>
      {v.subtitulo && <p className="lead">{v.subtitulo}</p>}
      {(temLink(v.botao) || temLink(v.botao_secundario)) && (
        <div className="hero__actions">
          {temLink(v.botao) && (
            <SmartLink href={v.botao.link} className={`btn${variante === "fundo" ? " btn--accent" : ""}`}>
              {v.botao.texto}
              <Icon name="arrow-right" size={16} />
            </SmartLink>
          )}
          {temLink(v.botao_secundario) && (
            <SmartLink href={v.botao_secundario.link} className="btn btn--ghost">
              {v.botao_secundario.texto}
            </SmartLink>
          )}
        </div>
      )}
    </div>
  );

  if (variante === "fundo") {
    return (
      <section className="hero hero--fundo">
        <div className="media hero__bg">
          <Img imagem={v.imagem} prioridade={primeiro} />
        </div>
        <div className="container">{copy}</div>
      </section>
    );
  }
  return (
    <section className={`hero hero--${variante}`}>
      <div className="container hero__grid">
        {copy}
        {v.imagem && (
          <div className="media hero__media">
            <Img imagem={v.imagem} sizes="(min-width: 900px) 50vw, 100vw" prioridade={primeiro} />
          </div>
        )}
      </div>
    </section>
  );
}

function Numeros({ v }: { v: any }) {
  return (
    <section className="section section--tight">
      <div className="container">
        <div className="stats" style={{ "--n": v.itens.length } as React.CSSProperties}>
          {v.itens.map((i: any) => (
            <div key={i.rotulo} className="stat">
              <span className="stat__valor">{i.valor}</span>
              <span className="stat__rotulo">{i.rotulo}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Destaques({ v }: { v: any }) {
  return (
    <section className="section">
      <div className="container">
        <SectionHead titulo={v.titulo} subtitulo={v.subtitulo} />
        <div className="grid grid--4">
          {v.itens.map((i: any) => (
            <div key={i.titulo} className="feature">
              <span className="feature__icon">
                <Icon name={i.icone} size={22} />
              </span>
              <h3 className="h3">{i.titulo}</h3>
              {i.texto && <p>{i.texto}</p>}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Texto({ v }: { v: any }) {
  return (
    <section className="section">
      <div className="container">
        <div className="grid" style={{ gap: 24 }}>
          {v.titulo && <h2 className="h2">{v.titulo}</h2>}
          <div className="prose" dangerouslySetInnerHTML={{ __html: v.corpo }} />
        </div>
      </div>
    </section>
  );
}

function ImagemTexto({ v }: { v: any }) {
  return (
    <section className="section">
      <div className={`container split${v.imagem_a_direita ? " split--direita" : ""}`}>
        <div className="media">
          <Img imagem={v.imagem} sizes="(min-width: 900px) 50vw, 100vw" />
        </div>
        <div className="stack" style={{ "--stack": "20px" } as React.CSSProperties}>
          <h2 className="h2">{v.titulo}</h2>
          <div className="prose muted" dangerouslySetInnerHTML={{ __html: v.corpo }} />
          {temLink(v.botao) && (
            <SmartLink href={v.botao.link} className="link-arrow">
              {v.botao.texto} <Icon name="arrow-right" size={16} />
            </SmartLink>
          )}
        </div>
      </div>
    </section>
  );
}

function Cta({ v }: { v: any }) {
  return (
    <section className="section">
      <div className="container">
        <div className={`cta${v.estilo === "suave" ? " cta--suave" : ""}`}>
          <div>
            <h2 className="h2">{v.titulo}</h2>
            {v.texto && <p className="lead">{v.texto}</p>}
          </div>
          {temLink(v.botao) && (
            <SmartLink href={v.botao.link} className="btn">
              {v.botao.texto}
              <Icon name="arrow-right" size={16} />
            </SmartLink>
          )}
        </div>
      </div>
    </section>
  );
}

function Galeria({ v }: { v: any }) {
  return (
    <section className="section">
      <div className="container">
        <SectionHead titulo={v.titulo} />
        <div className="gallery">
          {v.imagens.map((i: any, n: number) => (
            <figure key={i.imagem?.id ?? n} className="media">
              <Img imagem={i.imagem} sizes={n === 0 ? "(min-width: 760px) 50vw, 50vw" : "(min-width: 760px) 25vw, 50vw"} />
              {i.legenda && (
                <figcaption className="badge" style={{ position: "absolute" }}>
                  {i.legenda}
                </figcaption>
              )}
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}

function Dinamico({ bloco, ctx }: { bloco: Bloco; ctx: Ctx }) {
  const v = bloco.value;
  const itens: any[] = v.itens ?? [];
  if (itens.length === 0 && bloco.type !== "horario") return null;

  switch (bloco.type) {
    case "planos":
      return (
        <section className="section">
          <div className="container">
            <SectionHead titulo={v.titulo} subtitulo={v.subtitulo} acao={{ texto: "Comparar planos", href: "/planos" }} />
            <PlanGrid planos={itens} adesaoOnline={ctx.adesaoOnline} />
          </div>
        </section>
      );
    case "modalidades":
      return (
        <section className="section">
          <div className="container">
            <SectionHead titulo={v.titulo} subtitulo={v.subtitulo} acao={{ texto: "Todas as modalidades", href: "/modalidades" }} />
            <div className="grid grid--3">
              {itens.map((m) => (
                <ClassCard key={m.id} m={m} />
              ))}
            </div>
          </div>
        </section>
      );
    case "equipa":
      return (
        <section className="section">
          <div className="container">
            <SectionHead titulo={v.titulo} subtitulo={v.subtitulo} acao={{ texto: "Conhecer a equipa", href: "/equipa" }} />
            <div className="grid grid--4">
              {itens.map((t) => (
                <CoachCard key={t.id} t={t} />
              ))}
            </div>
          </div>
        </section>
      );
    case "testemunhos":
      return (
        <section className="section">
          <div className="container">
            <SectionHead titulo={v.titulo} subtitulo={v.subtitulo} />
            <Quotes itens={itens} />
          </div>
        </section>
      );
    case "faq":
      return (
        <section className="section">
          <div className="container faq-layout">
            <div>
              <h2 className="h2">{v.titulo || "Perguntas frequentes"}</h2>
              {v.subtitulo && (
                <p className="lead" style={{ marginTop: 16 }}>
                  {v.subtitulo}
                </p>
              )}
            </div>
            <Faq itens={itens} />
          </div>
        </section>
      );
    case "horario":
      return (
        <section className="section">
          <div className="container faq-layout">
            <div>
              <p className="eyebrow">Horário</p>
              <h2 className="h2">{v.titulo || "Aulas de hoje"}</h2>
              {v.subtitulo && (
                <p className="lead" style={{ marginTop: 16 }}>
                  {v.subtitulo}
                </p>
              )}
            </div>
            <TodaySchedule aulas={itens} />
          </div>
        </section>
      );
    default:
      return null;
  }
}

/** Renderiza os blocos do StreamField. Cada tipo de bloco do CMS tem aqui o seu componente. */
export function Blocks({ blocos, ctx }: { blocos: Bloco[]; ctx: Ctx }) {
  return (
    <>
      {blocos.map((bloco, i) => {
        const v = bloco.value;
        switch (bloco.type) {
          case "hero":
            return <Hero key={bloco.id} v={v} primeiro={i === 0} />;
          case "numeros":
            return <Numeros key={bloco.id} v={v} />;
          case "destaques":
            return <Destaques key={bloco.id} v={v} />;
          case "texto":
            return <Texto key={bloco.id} v={v} />;
          case "imagem_texto":
            return <ImagemTexto key={bloco.id} v={v} />;
          case "cta":
            return <Cta key={bloco.id} v={v} />;
          case "galeria":
            return <Galeria key={bloco.id} v={v} />;
          case "planos":
          case "modalidades":
          case "equipa":
          case "testemunhos":
          case "faq":
          case "horario":
            return <Dinamico key={bloco.id} bloco={bloco} ctx={ctx} />;
          default:
            if (process.env.NODE_ENV !== "production") {
              return (
                <div key={bloco.id} className="container empty">
                  Bloco “{bloco.type}” sem componente no site.
                </div>
              );
            }
            return null;
        }
      })}
    </>
  );
}
