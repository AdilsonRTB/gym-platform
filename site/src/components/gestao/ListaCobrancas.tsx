"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { pedido, useGestao } from "@/lib/cliente";
import { dataCurta, diasAte } from "@/lib/datas";
import { formatarCve } from "@/lib/format";
import type { Cobranca, Pagina } from "@/lib/gestaoTypes";

import { Icon } from "../Icon";
import { EstadoCobranca } from "./Estados";
import { ReceberPagamento } from "./ReceberPagamento";
import { useToast } from "./Toast";

const TABS = [
  { id: "atraso", nome: "Em atraso" },
  { id: "pendente", nome: "A vencer" },
  { id: "paga", nome: "Pagas" },
];

export function ListaCobrancas() {
  const router = useRouter();
  const estado = useSearchParams().get("estado") ?? "atraso";
  const [pagina, setPagina] = useState(1);
  const { dados, recarregar } = useGestao<Pagina<Cobranca>>(`cobrancas?estado=${estado}&page=${pagina}`);
  const [receber, setReceber] = useState<Cobranca | null>(null);
  const { mostrar, toast } = useToast();
  const total = dados?.results.reduce((soma, c) => soma + c.valor_cve, 0) ?? 0;

  return (
    <>
      <div className="p-head">
        <div>
          <h1>Cobranças</h1>
          <p>
            {dados ? `${dados.count} ${estado === "paga" ? "pagas" : "por receber"}` : "A carregar…"}
            {dados && estado !== "paga" && dados.count > 0 ? ` · ${formatarCve(total)} CVE nesta página` : ""}
          </p>
        </div>
      </div>

      <div className="filtros" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            className="chip"
            role="tab"
            aria-selected={estado === t.id}
            onClick={() => {
              setPagina(1);
              router.replace(`/gestao/cobrancas?estado=${t.id}`);
            }}
          >
            {t.nome}
          </button>
        ))}
      </div>

      <section className="bloco">
        {dados && dados.results.length === 0 && (
          <div className="bloco__vazio">{estado === "atraso" ? "Nenhuma mensalidade em atraso. 🎉" : "Nada para mostrar."}</div>
        )}
        <ul className="lista">
          {dados?.results.map((c) => (
            <li key={c.id} className="linha" style={{ flexWrap: "wrap" }}>
              <Link href={`/gestao/socios/${c.socio?.id}`} className="linha__principal">
                <strong>
                  #{c.socio?.numero} {c.socio?.nome}
                </strong>
                <span>
                  {c.descricao} ·{" "}
                  {c.estado === "paga"
                    ? `pago ${dataCurta(c.paga_em)}${c.fatura ? ` · ${c.fatura.numero}` : ""}`
                    : c.atrasada
                      ? `${-diasAte(c.vencimento)} dias de atraso`
                      : `vence ${dataCurta(c.vencimento)}`}
                </span>
              </Link>
              <span className="linha__lado num">{formatarCve(c.valor_cve)} CVE</span>
              <EstadoCobranca c={c} />
              {c.estado === "pendente" && (
                <span style={{ display: "flex", gap: 6 }}>
                  <button
                    className="icon-btn"
                    title="Enviar lembrete"
                    aria-label={`Enviar lembrete a ${c.socio?.nome}`}
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
        {dados && dados.count > 30 && (
          <div className="paginacao">
            <span>Página {pagina}</span>
            <span style={{ display: "flex", gap: 8 }}>
              <button className="btn btn--sm btn--ghost" disabled={!dados.previous} onClick={() => setPagina((p) => p - 1)}>
                Anterior
              </button>
              <button className="btn btn--sm btn--ghost" disabled={!dados.next} onClick={() => setPagina((p) => p + 1)}>
                Seguinte
              </button>
            </span>
          </div>
        )}
      </section>

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
