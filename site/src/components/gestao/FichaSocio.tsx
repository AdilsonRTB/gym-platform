"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import QRCode from "qrcode";
import { useEffect, useRef, useState } from "react";

import { pedido, useGestao } from "@/lib/cliente";
import { dataCurta, dataLonga, diasAte, quando } from "@/lib/datas";
import { formatarCve, iniciais, PERIODICIDADE } from "@/lib/format";
import type { Cobranca, Socio } from "@/lib/gestaoTypes";
import { registarEntrada } from "@/lib/offline";
import type { Plano } from "@/lib/types";

import { Icon } from "../Icon";
import { EstadoCobranca, EstadoSocio } from "./Estados";
import { ReceberPagamento } from "./ReceberPagamento";
import { useToast } from "./Toast";

function CartaoQR({ codigo, nome, numero }: { codigo: string; nome: string; numero: number }) {
  const [svg, setSvg] = useState("");
  useEffect(() => {
    QRCode.toString(codigo, { type: "svg", margin: 1, errorCorrectionLevel: "M" }).then(setSvg);
  }, [codigo]);

  function imprimir() {
    const w = window.open("", "_blank", "width=420,height=560");
    if (!w) return;
    w.document.write(
      `<html><head><title>Cartão ${numero}</title><style>body{font-family:system-ui;text-align:center;padding:24px}svg{width:240px}</style></head>` +
        `<body>${svg}<h2>${nome}</h2><p>Sócio nº ${numero}</p><script>print()</script></body></html>`,
    );
    w.document.close();
  }

  return (
    <div className="stack" style={{ "--stack": "12px" } as React.CSSProperties}>
      <div className="qr" dangerouslySetInnerHTML={{ __html: svg }} aria-label="Código QR do cartão de sócio" />
      <button className="btn btn--ghost btn--sm btn--block" onClick={imprimir}>
        Imprimir cartão
      </button>
    </div>
  );
}

export function FichaSocio({ id, planos }: { id: number; planos: Plano[] }) {
  const { dados: s, recarregar, erro } = useGestao<Socio>(`socios/${id}`);
  const [receber, setReceber] = useState<Cobranca | null>(null);
  const [mostrarQR, setMostrarQR] = useState(false);
  const dialogoPlano = useRef<HTMLDialogElement>(null);
  const { mostrar, toast } = useToast();
  const params = useSearchParams();

  useEffect(() => {
    if (params.get("novo")) mostrar("Sócio criado. Receba o primeiro pagamento para ativar a assinatura.");
  }, [params, mostrar]);

  if (erro) return <div className="bloco bloco__vazio">{erro}</div>;
  if (!s) return <p className="muted">A carregar…</p>;

  const a = s.assinatura;
  const pendentes = s.cobrancas.filter((c) => c.estado === "pendente");
  const pagas = s.cobrancas.filter((c) => c.estado === "paga");
  const DIAS_PERIODO: Record<string, number> = { semanal: 7, mensal: 30, trimestral: 91, semestral: 182, anual: 365, avulso: 1 };
  const restante = a ? Math.max(0, Math.min(100, (a.dias_restantes / (DIAS_PERIODO[a.periodicidade] ?? 30)) * 100)) : 0;

  async function acao(caminho: string, corpo: unknown, sucesso: string) {
    const r = await pedido("gestao", caminho, { corpo });
    if (r.ok) {
      mostrar(sucesso);
      recarregar();
    } else mostrar(r.erro ?? "Erro");
    return r;
  }

  async function checkinManual() {
    const r = await registarEntrada({ socio_id: s!.id });
    mostrar(r.permitido ? `Entrada registada · ${r.motivo}` : `Entrada recusada · ${r.motivo}`);
    recarregar();
  }

  async function mudarEstado(estado: string) {
    const r = await pedido("gestao", `socios/${s!.id}`, { metodo: "PATCH", corpo: { estado } });
    if (r.ok) {
      mostrar(estado === "ativo" ? "Sócio reativado" : estado === "suspenso" ? "Sócio suspenso" : "Sócio desativado");
      recarregar();
    }
  }

  return (
    <>
      <div className="p-head">
        <div>
          <Link href="/gestao/socios" className="small muted" style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
            <Icon name="voltar" size={14} /> Sócios
          </Link>
        </div>
        <div className="p-acoes">
          <button className="btn btn--ghost btn--sm" onClick={checkinManual}>
            <Icon name="check" size={16} /> Check-in manual
          </button>
          {pendentes[0] && (
            <button className="btn btn--sm" onClick={() => setReceber(pendentes[0])}>
              Receber {formatarCve(pendentes[0].valor_cve)} CVE
            </button>
          )}
        </div>
      </div>

      <div className="ficha">
        <div className="stack" style={{ "--stack": "16px" } as React.CSSProperties}>
          <section className="bloco bloco__corpo">
            <div className="ficha__id">
              <span className="avatar avatar--lg">{iniciais(s.nome)}</span>
              <div>
                <h1>{s.nome}</h1>
                <span className="muted small">
                  Sócio nº {s.numero} · desde {dataCurta(s.criado_em)}
                </span>
              </div>
            </div>
            <div style={{ margin: "16px 0" }}>
              <EstadoSocio s={s} />
            </div>
            <dl className="dados">
              <div>
                <dt>Telefone</dt>
                <dd>{s.telefone ? <a href={`tel:${s.telefone.replace(/\s/g, "")}`}>{s.telefone}</a> : "—"}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{s.email || "—"}</dd>
              </div>
              <div>
                <dt>NIF</dt>
                <dd>{s.nif || "—"}</dd>
              </div>
              <div>
                <dt>Nascimento</dt>
                <dd>{dataLonga(s.data_nascimento)}</dd>
              </div>
              <div>
                <dt>Emergência</dt>
                <dd>{s.contacto_emergencia || "—"}</dd>
              </div>
            </dl>
            {s.notas && (
              <p className="small" style={{ marginBottom: 0, padding: 12, borderRadius: 12, background: "var(--c-surface)" }}>
                {s.notas}
              </p>
            )}
          </section>

          <section className="bloco bloco__corpo">
            {mostrarQR ? (
              <CartaoQR codigo={s.codigo} nome={s.nome} numero={s.numero} />
            ) : (
              <button className="btn btn--ghost btn--block btn--sm" onClick={() => setMostrarQR(true)}>
                <Icon name="qr" size={16} /> Ver cartão QR
              </button>
            )}
            <div className="acoes-grelha" style={{ marginTop: 8 }}>
              <button
                className="btn btn--ghost btn--sm"
                onClick={() => {
                  if (confirm("Gerar um cartão novo? O cartão atual deixa de funcionar."))
                    acao(`socios/${s.id}/novo-codigo`, {}, "Cartão novo gerado");
                }}
              >
                Cartão perdido
              </button>
              {s.estado === "ativo" ? (
                <button className="btn btn--ghost btn--sm" onClick={() => mudarEstado("suspenso")}>
                  Suspender
                </button>
              ) : (
                <button className="btn btn--ghost btn--sm" onClick={() => mudarEstado("ativo")}>
                  Reativar
                </button>
              )}
            </div>
          </section>
        </div>

        <div className="stack" style={{ "--stack": "16px" } as React.CSSProperties}>
          <section className="bloco">
            <div className="bloco__topo">
              <h2>Assinatura</h2>
              <button className="btn btn--ghost btn--sm" onClick={() => dialogoPlano.current?.showModal()}>
                {a ? "Mudar plano" : "Escolher plano"}
              </button>
            </div>
            <div className="bloco__corpo">
              {a ? (
                <>
                  <div className="validade">
                    <div>
                      <span className="muted small">
                        {a.plano} · {formatarCve(a.preco_cve)} CVE {PERIODICIDADE[a.periodicidade]}
                      </span>
                      <div className="validade__data">{a.valida ? `Até ${dataLonga(a.data_fim)}` : "Expirada"}</div>
                    </div>
                    <span className="muted small">
                      {a.dias_restantes >= 0 ? `${a.dias_restantes} dias` : `${-a.dias_restantes} dias em atraso`}
                    </span>
                  </div>
                  <div className="progresso">
                    <span
                      style={{
                        width: `${a.dias_restantes >= 0 ? restante : 100}%`,
                        background: a.dias_restantes < 0 ? "var(--erro)" : undefined,
                      }}
                    />
                  </div>
                </>
              ) : (
                <p className="muted" style={{ margin: 0 }}>
                  Sem assinatura ativa.
                </p>
              )}
            </div>
          </section>

          <section className="bloco">
            <div className="bloco__topo">
              <h2>Mensalidades</h2>
              <span className="muted small">{pagas.length} pagas</span>
            </div>
            {s.cobrancas.length === 0 && <div className="bloco__vazio">Sem cobranças.</div>}
            <ul className="lista">
              {s.cobrancas.map((c) => (
                <li key={c.id} className="linha" style={{ flexWrap: "wrap" }}>
                  <span className="linha__principal">
                    <strong>{c.descricao}</strong>
                    <span>
                      {c.estado === "paga"
                        ? `Pago ${dataCurta(c.paga_em)}${c.metodo ? ` · ${c.metodo}` : ""}${c.fatura ? ` · ${c.fatura.numero}` : ""}`
                        : `Vence ${dataCurta(c.vencimento)}${c.atrasada ? ` · ${-diasAte(c.vencimento)} dias de atraso` : ""}`}
                    </span>
                  </span>
                  <span className="linha__lado num">{formatarCve(c.valor_cve)} CVE</span>
                  <EstadoCobranca c={c} />
                  {c.estado === "pendente" && (
                    <span style={{ display: "flex", gap: 6 }}>
                      <button
                        className="icon-btn"
                        title="Enviar lembrete"
                        aria-label="Enviar lembrete"
                        onClick={async () => {
                          const r = await pedido<{ canais: string[] }>("gestao", `cobrancas/${c.id}/lembrete`, { corpo: {} });
                          mostrar(r.ok ? `Lembrete enviado (${r.dados?.canais.join(", ")})` : (r.erro ?? "Erro"));
                        }}
                      >
                        <Icon name="sino" size={16} />
                      </button>
                      <button className="btn btn--sm" onClick={() => setReceber(c)}>
                        Receber
                      </button>
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </section>

          <section className="bloco">
            <div className="bloco__topo">
              <h2>Entradas recentes</h2>
            </div>
            {s.checkins.length === 0 && <div className="bloco__vazio">Ainda sem entradas.</div>}
            <ul className="lista">
              {s.checkins.map((c) => (
                <li key={c.id} className="linha">
                  <span className="linha__principal">
                    <strong>{quando(c.momento)}</strong>
                    <span>
                      {c.motivo}
                      {c.offline ? " · registado sem rede" : ""}
                    </span>
                  </span>
                  <span className={`estado ${c.permitido ? "estado--ok" : "estado--erro"}`}>
                    {c.permitido ? "Entrou" : "Recusado"}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>

      <dialog ref={dialogoPlano} className="dialogo" aria-labelledby="plano-titulo">
        <form
          className="dialogo__corpo"
          onSubmit={async (e) => {
            e.preventDefault();
            const plano = new FormData(e.currentTarget).get("plano");
            const r = await acao(`socios/${s.id}/assinatura`, { plano: Number(plano) }, "Plano alterado. Receba o pagamento para ativar.");
            if (r.ok) dialogoPlano.current?.close();
          }}
        >
          <h2 id="plano-titulo">Escolher plano</h2>
          <p className="muted small" style={{ margin: 0 }}>
            A assinatura atual é substituída e é criada a primeira cobrança do novo plano.
          </p>
          <div className="plan-options">
            {planos.map((p) => (
              <label key={p.id} className="plan-option">
                <input type="radio" name="plano" value={p.id} defaultChecked={p.id === a?.plano_id} required />
                <span className="plan-option__info">
                  <strong>{p.nome}</strong>
                </span>
                <span className="plan-option__preco">{formatarCve(p.preco_cve)} CVE</span>
              </label>
            ))}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn">Confirmar</button>
            <button type="button" className="btn btn--ghost" onClick={() => dialogoPlano.current?.close()}>
              Cancelar
            </button>
          </div>
        </form>
      </dialog>

      <ReceberPagamento
        cobranca={receber ? { ...receber, socio: { id: s.id, numero: s.numero, nome: s.nome, telefone: s.telefone } } : null}
        aoFechar={() => setReceber(null)}
        aoPagar={(c) => {
          setReceber(null);
          mostrar(`Pagamento registado${c.fatura ? ` · fatura ${c.fatura.numero}` : ""}`);
          recarregar();
        }}
      />
      {toast}
    </>
  );
}
