"use client";

import { useState } from "react";

import { Field, Sucesso } from "./Field";
import { useSubmit } from "./useSubmit";

/** Pedido de acesso ou eliminação de dados pessoais (CNPD). */
export function DataRequestForm() {
  const [enviado, setEnviado] = useState(false);
  const { enviar, aEnviar, erros } = useSubmit("pedidos-dados");

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const ok = await enviar({ tipo: f.get("tipo"), nome: f.get("nome"), email: f.get("email"), telefone: f.get("telefone") });
    if (ok) setEnviado(true);
  }

  if (enviado) {
    return <Sucesso titulo="Pedido registado" texto="Vamos responder por email no prazo legal." />;
  }
  return (
    <form className="form" onSubmit={onSubmit} noValidate>
      <Field id="pd-tipo" label="O que pretende?" erro={erros.tipo}>
        <select id="pd-tipo" name="tipo" className="select" defaultValue="exportacao">
          <option value="exportacao">Receber uma cópia dos meus dados</option>
          <option value="eliminacao">Eliminar os meus dados</option>
        </select>
      </Field>
      <div className="form__row">
        <Field id="pd-nome" label="Nome" erro={erros.nome} opcional>
          <input id="pd-nome" name="nome" className="input" autoComplete="name" />
        </Field>
        <Field id="pd-telefone" label="Telefone" erro={erros.telefone} opcional>
          <input id="pd-telefone" name="telefone" type="tel" className="input" autoComplete="tel" />
        </Field>
      </div>
      <Field id="pd-email" label="Email usado no ginásio" erro={erros.email}>
        <input id="pd-email" name="email" type="email" className="input" autoComplete="email" required />
      </Field>
      {erros.geral && (
        <p className="erro" role="alert">
          {erros.geral}
        </p>
      )}
      <div>
        <button className="btn btn--ghost" disabled={aEnviar}>
          {aEnviar ? "A enviar…" : "Enviar pedido"}
        </button>
      </div>
    </form>
  );
}
