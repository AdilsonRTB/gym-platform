"use client";

import { useState } from "react";

import { pedido } from "@/lib/cliente";

import { Icon } from "../Icon";

type Inicio = { pagamento: { tipo: "redirect" | "form_post"; url: string; campos: Record<string, string> } };

/** Paga uma mensalidade online (Vinti4Net via SISP, ou o fornecedor configurado). */
export function PagarCobranca({ uuid }: { uuid: string }) {
  const [aPagar, setAPagar] = useState(false);
  const [erro, setErro] = useState<string>();

  async function pagar() {
    setAPagar(true);
    setErro(undefined);
    const r = await pedido<Inicio>("app", `cobrancas/${uuid}/pagar`, { corpo: {} });
    if (!r.ok || !r.dados) {
      setErro(r.erro);
      setAPagar(false);
      return;
    }
    const { tipo, url, campos } = r.dados.pagamento;
    if (tipo === "redirect") {
      window.location.assign(url);
      return;
    }
    const form = document.createElement("form");
    form.method = "POST";
    form.action = url;
    for (const [nome, valor] of Object.entries(campos)) {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = nome;
      input.value = valor;
      form.appendChild(input);
    }
    document.body.appendChild(form);
    form.submit();
  }

  return (
    <div>
      <button className="btn btn--block" onClick={pagar} disabled={aPagar}>
        {aPagar ? "A abrir o pagamento…" : "Pagar com Vinti4"}
        {!aPagar && <Icon name="arrow-right" size={16} />}
      </button>
      {erro && (
        <p className="erro" style={{ marginTop: 8 }}>
          {erro}
        </p>
      )}
    </div>
  );
}
