import Link from "next/link";
import { redirect } from "next/navigation";
import QRCode from "qrcode";

import { PagarCobranca } from "@/components/app/PagarCobranca";
import { Sair } from "@/components/app/Sair";
import { Icon } from "@/components/Icon";
import { dataCurta, dataLonga, quando } from "@/lib/datas";
import { formatarCve, PERIODICIDADE } from "@/lib/format";
import type { Assinatura, CheckIn, Cobranca } from "@/lib/gestaoTypes";
import { carregarSite } from "@/lib/site";
import { apiPrivada } from "@/lib/sessao";

type Eu = {
  socio: { numero: number; nome: string; codigo: string; estado: string; desde: string };
  assinatura: Assinatura | null;
  por_pagar: Cobranca[];
  pagamentos: Cobranca[];
  checkins: CheckIn[];
  checkins_mes: number;
};

type Props = { params: Promise<{ domain: string }>; searchParams: Promise<{ pagamento?: string }> };

export default async function AppSocio({ params, searchParams }: Props) {
  const { site, domain } = await carregarSite((await params).domain);
  const { status, dados: eu } = await apiPrivada<Eu>("app", domain, "/eu/");
  if (status !== 200 || !eu) redirect("/app/entrar");
  const { pagamento } = await searchParams;

  const qr = await QRCode.toString(eu.socio.codigo, { type: "svg", margin: 1, errorCorrectionLevel: "M" });
  const a = eu.assinatura;
  const valida = eu.socio.estado === "ativo" && a?.valida;
  const primeiroNome = eu.socio.nome.split(" ")[0];

  return (
    <main className="app">
      <div className="app__topo">
        <span className="muted small">{site.nome}</span>
        <Sair />
      </div>
      <h1 className="app__ola">Olá, {primeiroNome}</h1>

      {pagamento && (
        <div className="notice" role="status">
          <span className="notice__icon">
            <Icon name={eu.por_pagar.length ? "alerta" : "check"} />
          </span>
          <div>
            <strong>{eu.por_pagar.length ? "O pagamento não foi concluído" : "Pagamento recebido"}</strong>
            <p className="muted small" style={{ margin: "4px 0 0" }}>
              {eu.por_pagar.length ? "Não foi cobrado nenhum valor. Pode tentar novamente." : "Obrigado! A fatura foi enviada por email."}
            </p>
          </div>
        </div>
      )}

      <section className="cartao-socio" aria-label="Cartão de sócio">
        <div className="cartao-socio__topo">
          <span className="cartao-socio__ginasio">{site.nome}</span>
          <span className="cartao-socio__num">Nº {eu.socio.numero}</span>
        </div>
        <div className="qr" dangerouslySetInnerHTML={{ __html: qr }} role="img" aria-label="Código QR para a entrada" />
        <div className="cartao-socio__rodape">
          <div>
            <div className="cartao-socio__nome">{eu.socio.nome}</div>
            <small>{a ? `${a.plano} · até ${dataLonga(a.data_fim)}` : "Sem plano ativo"}</small>
          </div>
          <span className={`pill ${valida ? "pill--ok" : "pill--erro"}`}>{valida ? "Ativo" : "Inativo"}</span>
        </div>
      </section>
      <p className="muted small" style={{ margin: "-8px 0 0", textAlign: "center" }}>
        Mostre este código na receção para entrar.
      </p>

      {eu.por_pagar.length > 0 && (
        <section className="app-seccao">
          <h2>Por pagar</h2>
          <div className="app-cartao">
            {eu.por_pagar.map((c) => (
              <div key={c.uuid} className="cobranca-app">
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
                  <div>
                    <div className="cobranca-app__valor">{formatarCve(c.valor_cve)} CVE</div>
                    <span className="muted small">{c.descricao}</span>
                  </div>
                  <span className={`estado ${c.atrasada ? "estado--erro" : "estado--aviso"}`}>
                    {c.atrasada ? "Em atraso" : `Vence ${dataCurta(c.vencimento)}`}
                  </span>
                </div>
                {site.adesao_online ? (
                  <PagarCobranca uuid={c.uuid} />
                ) : (
                  <p className="muted small" style={{ margin: 0 }}>
                    Pague na receção em numerário, TPA ou transferência.
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="mini-stats">
        <div>
          <strong>{eu.checkins_mes}</strong>
          <span>treinos este mês</span>
        </div>
        <div>
          <strong>{a ? Math.max(0, a.dias_restantes) : 0}</strong>
          <span>dias de assinatura</span>
        </div>
      </section>

      {a && (
        <section className="app-seccao">
          <h2>Plano</h2>
          <div className="app-cartao">
            <div className="linha">
              <span className="linha__principal">
                <strong>{a.plano}</strong>
                <span>
                  {formatarCve(a.preco_cve)} CVE {PERIODICIDADE[a.periodicidade]}
                </span>
              </span>
              <Link href="/horario" className="btn btn--sm btn--ghost">
                Horário
              </Link>
            </div>
          </div>
        </section>
      )}

      {eu.checkins.length > 0 && (
        <section className="app-seccao">
          <h2>Últimos treinos</h2>
          <div className="app-cartao">
            {eu.checkins.slice(0, 5).map((c) => (
              <div key={c.id} className="linha">
                <Icon name="check" size={16} />
                <span className="linha__principal">
                  <strong>{quando(c.momento)}</strong>
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {eu.pagamentos.length > 0 && (
        <section className="app-seccao">
          <h2>Pagamentos</h2>
          <div className="app-cartao">
            {eu.pagamentos.slice(0, 6).map((c) => (
              <div key={c.uuid} className="linha">
                <span className="linha__principal">
                  <strong>{c.descricao}</strong>
                  <span>
                    {dataCurta(c.paga_em)}
                    {c.fatura ? ` · Fatura ${c.fatura.numero}` : ""}
                  </span>
                </span>
                <span className="linha__lado num">{formatarCve(c.valor_cve)} CVE</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <p className="muted small" style={{ textAlign: "center" }}>
        Sócio desde {dataLonga(eu.socio.desde)} · <Link href="/">{site.nome}</Link>
      </p>
    </main>
  );
}
