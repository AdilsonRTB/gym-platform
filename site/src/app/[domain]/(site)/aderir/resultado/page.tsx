import type { Metadata } from "next";
import Link from "next/link";

import { Icon } from "@/components/Icon";
import { getAdesao } from "@/lib/api";
import { formatarCve } from "@/lib/format";
import { carregarSite } from "@/lib/site";

type Props = { params: Promise<{ domain: string }>; searchParams: Promise<{ ref?: string }> };

export const metadata: Metadata = { title: "Adesão", robots: { index: false } };

export default async function Resultado({ params, searchParams }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const { ref } = await searchParams;
  const adesao = ref ? await getAdesao(domain, ref) : null;
  const paga = adesao?.estado === "paga";

  return (
    <section className="container page-head" style={{ maxWidth: 720 }}>
      <ol className="steps" aria-label="Passos">
        <li>
          <span className="steps__n">1</span>Plano e dados
        </li>
        <li>
          <span className="steps__n">2</span>Pagamento
        </li>
        <li aria-current={paga ? "step" : undefined}>
          <span className="steps__n">3</span>Bem-vindo
        </li>
      </ol>
      {paga ? (
        <>
          <h1 className="h1">Bem-vindo(a), {adesao.nome}!</h1>
          <p className="lead">
            O pagamento de {formatarCve(adesao.valor_cve)} CVE do plano {adesao.plano} foi confirmado. Enviámos a
            confirmação{adesao.fatura ? ` e a fatura ${adesao.fatura.numero}` : ""} para o seu email.
          </p>
          <div className="notice" style={{ marginTop: 40 }}>
            <span className="notice__icon">
              <Icon name="check" />
            </span>
            <div>
              <strong>Próximo passo</strong>
              <p className="muted" style={{ margin: "4px 0 0" }}>
                Apareça na receção com um documento de identificação para fazer a avaliação física e levantar o cartão.
              </p>
            </div>
          </div>
          <div className="hero__actions">
            <Link href="/horario" className="btn">
              Ver horário das aulas
            </Link>
            <Link href="/" className="btn btn--ghost">
              Voltar ao início
            </Link>
          </div>
        </>
      ) : (
        <>
          <h1 className="h1">{adesao?.estado === "pendente" ? "Pagamento em curso" : "O pagamento não foi concluído"}</h1>
          <p className="lead">
            {adesao?.estado === "pendente"
              ? "Ainda estamos à espera da confirmação da SISP. Atualize esta página dentro de alguns segundos."
              : "Não foi cobrado nenhum valor. Pode tentar novamente ou falar connosco."}
          </p>
          <div className="hero__actions">
            <Link href="/aderir" className="btn">
              Tentar novamente
            </Link>
            <Link href="/contactos" className="btn btn--ghost">
              Falar com {site.nome}
            </Link>
          </div>
        </>
      )}
    </section>
  );
}
