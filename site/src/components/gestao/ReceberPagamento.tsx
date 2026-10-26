"use client";

import { useEffect, useRef, useState } from "react";

import { pedido } from "@/lib/cliente";
import { formatarCve } from "@/lib/format";
import type { Cobranca } from "@/lib/gestaoTypes";

import { Icon } from "../Icon";

const METODOS = [
  { id: "numerario", nome: "Numerário" },
  { id: "tpa", nome: "TPA / cartão" },
  { id: "transferencia", nome: "Transferência" },
];

/** Diálogo para receber uma cobrança na receção. A fatura é emitida automaticamente. */
export function ReceberPagamento({
  cobranca,
  aoFechar,
  aoPagar,
}: {
  cobranca: Cobranca | null;
  aoFechar: () => void;
  aoPagar: (c: Cobranca) => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [aEnviar, setAEnviar] = useState<string | null>(null);
  const [erro, setErro] = useState<string>();

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (cobranca && !d.open) d.showModal();
    if (!cobranca && d.open) d.close();
  }, [cobranca]);

  async function pagar(metodo: string) {
    if (!cobranca) return;
    setAEnviar(metodo);
    setErro(undefined);
    const r = await pedido<Cobranca>("gestao", `cobrancas/${cobranca.id}/pagar`, { corpo: { metodo } });
    setAEnviar(null);
    if (r.ok && r.dados) aoPagar(r.dados);
    else setErro(r.erro);
  }

  return (
    <dialog ref={ref} className="dialogo" onClose={aoFechar} aria-labelledby="receber-titulo">
      {cobranca && (
        <div className="dialogo__corpo">
          <div>
            <h2 id="receber-titulo">Receber pagamento</h2>
            <p className="muted small" style={{ margin: "4px 0 0" }}>
              {cobranca.socio ? `${cobranca.socio.nome} · ` : ""}
              {cobranca.descricao}
            </p>
          </div>
          <div className="resumo__total" style={{ borderTop: 0, paddingTop: 0 }}>
            <span>Total</span>
            <strong>{formatarCve(cobranca.valor_cve)} CVE</strong>
          </div>
          <div className="metodos">
            {METODOS.map((m) => (
              <button key={m.id} onClick={() => pagar(m.id)} disabled={aEnviar !== null}>
                {m.nome}
                {aEnviar === m.id ? <span className="muted small">A registar…</span> : <Icon name="arrow-right" size={16} />}
              </button>
            ))}
          </div>
          {erro && <p className="erro">{erro}</p>}
          <p className="muted small" style={{ margin: 0 }}>
            A fatura é emitida e enviada ao sócio automaticamente.
          </p>
          <button className="btn btn--ghost" onClick={() => ref.current?.close()}>
            Cancelar
          </button>
        </div>
      )}
    </dialog>
  );
}
