"use client";

import { useState } from "react";

import type { ModalidadeResumo } from "@/lib/types";

import { Icon } from "../Icon";
import { Consentimento, Field, Honeypot, Sucesso } from "./Field";
import { useSubmit } from "./useSubmit";

type Props = {
  modalidades: Pick<ModalidadeResumo, "slug" | "nome">[];
  textoConsentimento: string;
  tipoInicial?: "contacto" | "aula_experimental";
  modalidadeInicial?: string;
  mensagemInicial?: string;
};

export function LeadForm({ modalidades, textoConsentimento, tipoInicial = "contacto", modalidadeInicial, mensagemInicial }: Props) {
  const [tipo, setTipo] = useState(tipoInicial);
  const [enviado, setEnviado] = useState(false);
  const { enviar, aEnviar, erros } = useSubmit("leads");

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const ok = await enviar({
      tipo,
      nome: f.get("nome"),
      email: f.get("email"),
      telefone: f.get("telefone"),
      mensagem: f.get("mensagem") ?? "",
      modalidade: tipo === "aula_experimental" ? f.get("modalidade") || null : null,
      data_preferida: tipo === "aula_experimental" ? f.get("data_preferida") || null : null,
      origem: window.location.pathname + window.location.search,
      consentimento: f.get("consentimento") === "on",
      website: f.get("website"),
    });
    if (ok) setEnviado(true);
  }

  if (enviado) {
    return (
      <Sucesso
        titulo={tipo === "aula_experimental" ? "Pedido de aula recebido!" : "Mensagem enviada!"}
        texto="Obrigado. A nossa equipa entra em contacto consigo em breve."
      />
    );
  }

  const hoje = new Date().toISOString().slice(0, 10);

  return (
    <form className="form" onSubmit={onSubmit} noValidate>
      <div className="segmented" role="group" aria-label="Tipo de pedido">
        <button type="button" aria-pressed={tipo === "aula_experimental"} onClick={() => setTipo("aula_experimental")}>
          Aula experimental
        </button>
        <button type="button" aria-pressed={tipo === "contacto"} onClick={() => setTipo("contacto")}>
          Contacto
        </button>
      </div>

      <Field id="nome" label="Nome" erro={erros.nome}>
        <input id="nome" name="nome" className="input" autoComplete="name" required />
      </Field>
      <div className="form__row">
        <Field id="telefone" label="Telefone / WhatsApp" erro={erros.telefone}>
          <input id="telefone" name="telefone" type="tel" className="input" autoComplete="tel" inputMode="tel" />
        </Field>
        <Field id="email" label="Email" erro={erros.email}>
          <input id="email" name="email" type="email" className="input" autoComplete="email" />
        </Field>
      </div>

      {tipo === "aula_experimental" && (
        <div className="form__row">
          <Field id="modalidade" label="Modalidade" erro={erros.modalidade} opcional>
            <select id="modalidade" name="modalidade" className="select" defaultValue={modalidadeInicial ?? ""}>
              <option value="">Ainda não sei</option>
              {modalidades.map((m) => (
                <option key={m.slug} value={m.slug}>
                  {m.nome}
                </option>
              ))}
            </select>
          </Field>
          <Field id="data_preferida" label="Data preferida" erro={erros.data_preferida} opcional>
            <input id="data_preferida" name="data_preferida" type="date" min={hoje} className="input" />
          </Field>
        </div>
      )}

      <Field id="mensagem" label="Mensagem" erro={erros.mensagem} opcional>
        <textarea id="mensagem" name="mensagem" className="textarea" defaultValue={mensagemInicial} />
      </Field>

      <Honeypot />
      <Consentimento texto={textoConsentimento} erro={erros.consentimento} />
      {erros.geral && (
        <p className="erro" role="alert">
          {erros.geral}
        </p>
      )}
      <div>
        <button className="btn" disabled={aEnviar}>
          {aEnviar ? "A enviar…" : tipo === "aula_experimental" ? "Marcar aula experimental" : "Enviar mensagem"}
          {!aEnviar && <Icon name="arrow-right" size={16} />}
        </button>
      </div>
    </form>
  );
}
