"use client";

import Link from "next/link";
import { useState } from "react";

import { useGestao } from "@/lib/cliente";
import { dataCurta, quando } from "@/lib/datas";
import { formatarCve } from "@/lib/format";
import type { Cobranca, Resumo } from "@/lib/gestaoTypes";

import { Icon } from "../Icon";
import { EstadoCobranca } from "./Estados";
import { ReceberPagamento } from "./ReceberPagamento";
import { useToast } from "./Toast";

function saudacao() {
  const h = Number(new Intl.DateTimeFormat("en-GB", { hour: "numeric", timeZone: "Atlantic/Cape_Verde" }).format(new Date()));
  return h < 12 ? "Bom dia" : h < 19 ? "Boa tarde" : "Boa noite";
}

export function PainelInicio() {
  const { dados: r, recarregar } = useGestao<Resumo>("resumo");
  const [receber, setReceber] = useState<Cobranca | null>(null);
  const { mostrar, toast } = useToast();
  const horas = r?.checkins_por_hora.slice(6, 24) ?? Array(18).fill(0);
  const maximo = Math.max(1, ...horas);
  const horaAtual = Number(new Intl.DateTimeFormat("en-GB", { hour: "numeric", timeZone: "Atlantic/Cape_Verde" }).format(new Date()));

  return (
    <>
      <div className="p-head">
        <div>
          <h1>{saudacao()}</h1>
          <p>Resumo de hoje no ginásio.</p>
        </div>
        <div className="p-acoes">
          <Link href="/gestao/socios/novo" className="btn btn--ghost btn--sm">
            Novo sócio
          </Link>
          <Link href="/gestao/checkin" className="btn btn--sm">
            <Icon name="qr" size={16} /> Check-in
          </Link>
        </div>
      </div>

      <div className="kpis">
        <Link href="/gestao/socios?estado=ativo" className="kpi">
          <span className="kpi__rotulo">Sócios ativos</span>
          <span className="kpi__valor">{r?.socios_ativos ?? "–"}</span>
          <span className="kpi__extra">de {r?.socios_total ?? "–"} registados</span>
        </Link>
        <Link href="/gestao/checkin" className="kpi">
          <span className="kpi__rotulo">Entradas hoje</span>
          <span className="kpi__valor">{r?.checkins_hoje ?? "–"}</span>
          <span className="kpi__extra">{r?.checkins_negados_hoje ? `${r.checkins_negados_hoje} recusadas` : "nenhuma recusada"}</span>
        </Link>
        <Link href="/gestao/cobrancas" className={`kpi${r?.em_atraso.n ? " kpi--alerta" : ""}`}>
          <span className="kpi__rotulo">Em atraso</span>
          <span className="kpi__valor">{r?.em_atraso.n ?? "–"}</span>
          <span className="kpi__extra">{r ? `${formatarCve(r.em_atraso.total ?? 0)} CVE por receber` : " "}</span>
        </Link>
        <div className="kpi">
          <span className="kpi__rotulo">Recebido este mês</span>
          <span className="kpi__valor">{r ? formatarCve(r.receita_mes) : "–"}</span>
          <span className="kpi__extra">CVE</span>
        </div>
      </div>

      <div className="paineis">
        <section className="bloco">
          <div className="bloco__topo">
            <h2>Entradas por hora</h2>
            <span className="muted small">06h – 23h</span>
          </div>
          <div className="bloco__corpo">
            <div className="barras" role="img" aria-label="Entradas por hora hoje">
              {horas.map((n, i) => (
                <div key={i} className="barras__col" title={`${i + 6}h: ${n} entradas`}>
                  <div
                    className={`barras__barra${i + 6 === horaAtual ? " barras__barra--ativa" : ""}`}
                    style={{ height: `${(n / maximo) * 100}%`, background: n && i + 6 !== horaAtual ? "var(--c-subtle)" : undefined }}
                  />
                  <span className="barras__hora">{i % 3 === 0 ? i + 6 : " "}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bloco__topo" style={{ borderTop: "1px solid var(--c-line)" }}>
            <h2>Últimas entradas</h2>
            <Link href="/gestao/checkin" className="small muted">
              Ver todas
            </Link>
          </div>
          {r && r.ultimos_checkins.length === 0 && <div className="bloco__vazio">Ainda não houve entradas hoje.</div>}
          <ul className="lista">
            {r?.ultimos_checkins.map((c) => (
              <li key={c.id}>
                <Link href={c.socio ? `/gestao/socios/${c.socio.id}` : "#"} className="linha">
                  <span className="hora">{quando(c.momento).replace("Hoje, ", "")}</span>
                  <span className="linha__principal">
                    <strong>{c.socio?.nome ?? "Cartão desconhecido"}</strong>
                    <span>{c.motivo}</span>
                  </span>
                  <span className={`estado ${c.permitido ? "estado--ok" : "estado--erro"}`}>
                    {c.permitido ? "Entrou" : "Recusado"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="bloco">
          <div className="bloco__topo">
            <h2>A vencer esta semana</h2>
            <Link href="/gestao/cobrancas?estado=pendente" className="small muted">
              Ver todas
            </Link>
          </div>
          {r && r.a_vencer.length === 0 && <div className="bloco__vazio">Nenhuma mensalidade a vencer.</div>}
          <ul className="lista">
            {r?.a_vencer.map((c) => (
              <li key={c.id} className="linha">
                <span className="linha__principal">
                  <strong>{c.socio?.nome}</strong>
                  <span>
                    {dataCurta(c.vencimento)} · {formatarCve(c.valor_cve)} CVE
                  </span>
                </span>
                <EstadoCobranca c={c} />
                <button className="btn btn--sm btn--ghost" onClick={() => setReceber(c)}>
                  Receber
                </button>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <ReceberPagamento
        cobranca={receber}
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
