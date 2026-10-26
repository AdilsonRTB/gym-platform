"use client";

import { useState } from "react";

import { formatarCve, PERIODICIDADE } from "@/lib/format";
import type { Plano } from "@/lib/types";

import { Icon } from "../Icon";
import { Consentimento, Field } from "./Field";
import { useSubmit } from "./useSubmit";

type RespostaAdesao = {
  ref: string;
  pagamento: { tipo: "redirect" | "form_post"; url: string; campos: Record<string, string> };
};

/** Submete o formulário do fornecedor (ex.: Vinti4Net) ou redireciona. */
function irParaPagamento({ tipo, url, campos }: RespostaAdesao["pagamento"]) {
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

export function JoinFlow({
  planos,
  planoInicial,
  textoConsentimento,
}: {
  planos: Plano[];
  planoInicial?: number;
  textoConsentimento: string;
}) {
  const [planoId, setPlanoId] = useState<number>(
    planos.find((p) => p.id === planoInicial)?.id ?? planos.find((p) => p.destaque)?.id ?? planos[0]?.id,
  );
  const [aRedirecionar, setARedirecionar] = useState(false);
  const { enviar, aEnviar, erros } = useSubmit<RespostaAdesao>("adesoes");
  const plano = planos.find((p) => p.id === planoId);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const resposta = await enviar({
      plano: planoId,
      nome: f.get("nome"),
      email: f.get("email"),
      telefone: f.get("telefone"),
      nif: f.get("nif") ?? "",
      morada: f.get("morada") ?? "",
      consentimento: f.get("consentimento") === "on",
    });
    if (resposta) {
      setARedirecionar(true);
      irParaPagamento(resposta.pagamento);
    }
  }

  const ocupado = aEnviar || aRedirecionar;

  return (
    <form className="checkout" onSubmit={onSubmit} noValidate>
      <div className="stack" style={{ "--stack": "40px" } as React.CSSProperties}>
        <fieldset style={{ border: 0, padding: 0, marginInline: 0, minWidth: 0 }}>
          <legend className="h3" style={{ marginBottom: 16 }}>
            1. Escolha o plano
          </legend>
          <div className="plan-options">
            {planos.map((p) => (
              <label key={p.id} className="plan-option">
                <input type="radio" name="plano" value={p.id} checked={p.id === planoId} onChange={() => setPlanoId(p.id)} />
                <span className="plan-option__info">
                  <strong>{p.nome}</strong>
                  {p.destaque && (
                    <span className="badge badge--accent" style={{ marginLeft: 8 }}>
                      Mais escolhido
                    </span>
                  )}
                  {p.descricao && <span className="muted small" style={{ display: "block" }}>{p.descricao}</span>}
                </span>
                <span className="plan-option__preco">
                  {formatarCve(p.preco_cve)} CVE
                  <span className="muted small" style={{ display: "block", fontWeight: 400 }}>
                    {PERIODICIDADE[p.periodicidade]}
                  </span>
                </span>
              </label>
            ))}
          </div>
          {erros.plano && <p className="erro">{erros.plano}</p>}
        </fieldset>

        <fieldset className="form" style={{ border: 0, padding: 0, marginInline: 0, minWidth: 0 }}>
          <legend className="h3" style={{ marginBottom: 16 }}>
            2. Os seus dados
          </legend>
          <Field id="nome" label="Nome completo" erro={erros.nome}>
            <input id="nome" name="nome" className="input" autoComplete="name" required />
          </Field>
          <div className="form__row">
            <Field id="email" label="Email" erro={erros.email}>
              <input id="email" name="email" type="email" className="input" autoComplete="email" required />
            </Field>
            <Field id="telefone" label="Telefone" erro={erros.telefone}>
              <input id="telefone" name="telefone" type="tel" className="input" autoComplete="tel" required />
            </Field>
          </div>
          <div className="form__row">
            <Field id="nif" label="NIF (para a fatura)" erro={erros.nif} opcional>
              <input id="nif" name="nif" className="input" inputMode="numeric" pattern="\d{9}" maxLength={9} />
            </Field>
            <Field id="morada" label="Morada" erro={erros.morada} opcional>
              <input id="morada" name="morada" className="input" autoComplete="street-address" />
            </Field>
          </div>
          <Consentimento texto={textoConsentimento} erro={erros.consentimento} />
        </fieldset>
      </div>

      <aside className="checkout__resumo">
        <div className="card resumo">
          <h2 className="h3">Resumo</h2>
          {plano && (
            <>
              <dl>
                <dt>{plano.nome}</dt>
                <dd>{formatarCve(plano.preco_cve)} CVE</dd>
                {plano.taxa_inscricao_cve > 0 && (
                  <>
                    <dt>Taxa de inscrição</dt>
                    <dd>{formatarCve(plano.taxa_inscricao_cve)} CVE</dd>
                  </>
                )}
              </dl>
              <div className="resumo__total">
                <span>Total</span>
                <strong>{formatarCve(plano.preco_cve + plano.taxa_inscricao_cve)} CVE</strong>
              </div>
            </>
          )}
          {erros.geral && (
            <p className="erro" role="alert" style={{ marginTop: 16 }}>
              {erros.geral}
            </p>
          )}
          <button className="btn btn--block" style={{ marginTop: 24 }} disabled={ocupado || !plano}>
            {aRedirecionar ? "A abrir o pagamento…" : aEnviar ? "A confirmar…" : "Pagar com Vinti4"}
            {!ocupado && <Icon name="arrow-right" size={16} />}
          </button>
          <p className="seguro">
            <Icon name="escudo" size={16} />
            Pagamento seguro SISP. Fatura enviada por email.
          </p>
        </div>
      </aside>
    </form>
  );
}
