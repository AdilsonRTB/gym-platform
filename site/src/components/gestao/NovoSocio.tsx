"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { formatarCve, PERIODICIDADE } from "@/lib/format";
import type { Plano } from "@/lib/types";

import { Field } from "../forms/Field";
import { Icon } from "../Icon";

export function NovoSocio({ planos }: { planos: Plano[] }) {
  const router = useRouter();
  const [erros, setErros] = useState<Record<string, string>>({});
  const [aGuardar, setAGuardar] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setAGuardar(true);
    const f = new FormData(e.currentTarget);
    const corpo = Object.fromEntries(
      ["nome", "telefone", "email", "nif", "data_nascimento", "morada", "contacto_emergencia", "notas"].map((k) => [
        k,
        (f.get(k) as string) || (k === "data_nascimento" ? null : ""),
      ]),
    );
    const res = await fetch("/api/gestao/socios", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...corpo, plano: f.get("plano") ? Number(f.get("plano")) : null, consentimento: f.get("consentimento") === "on" }),
    });
    const dados = await res.json().catch(() => ({}));
    if (res.ok) {
      router.push(`/gestao/socios/${dados.socio.id}?novo=1`);
      return;
    }
    const e2: Record<string, string> = {};
    for (const [k, v] of Object.entries(dados)) e2[k] = Array.isArray(v) ? String(v[0]) : String(v);
    setErros(e2);
    setAGuardar(false);
  }

  return (
    <>
      <div className="p-head">
        <div>
          <Link href="/gestao/socios" className="small muted" style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
            <Icon name="voltar" size={14} /> Sócios
          </Link>
          <h1 style={{ marginTop: 8 }}>Novo sócio</h1>
          <p>Depois de guardar, pode receber já o primeiro pagamento.</p>
        </div>
      </div>

      <form className="ficha" onSubmit={onSubmit} noValidate>
        <section className="bloco">
          <div className="bloco__topo">
            <h2>Plano</h2>
          </div>
          <div className="bloco__corpo plan-options">
            {planos.map((p) => (
              <label key={p.id} className="plan-option">
                <input type="radio" name="plano" value={p.id} defaultChecked={p.destaque} />
                <span className="plan-option__info">
                  <strong>{p.nome}</strong>
                  {p.taxa_inscricao_cve > 0 && (
                    <span className="muted small" style={{ display: "block" }}>
                      + {formatarCve(p.taxa_inscricao_cve)} CVE inscrição
                    </span>
                  )}
                </span>
                <span className="plan-option__preco">
                  {formatarCve(p.preco_cve)}
                  <span className="muted small" style={{ display: "block", fontWeight: 400 }}>
                    {PERIODICIDADE[p.periodicidade]}
                  </span>
                </span>
              </label>
            ))}
            <label className="plan-option">
              <input type="radio" name="plano" value="" />
              <span className="plan-option__info">
                <strong>Sem plano por agora</strong>
              </span>
            </label>
          </div>
        </section>

        <section className="bloco">
          <div className="bloco__topo">
            <h2>Dados pessoais</h2>
          </div>
          <div className="bloco__corpo form">
            <Field id="nome" label="Nome completo" erro={erros.nome}>
              <input id="nome" name="nome" className="input" required autoFocus />
            </Field>
            <div className="form__row">
              <Field id="telefone" label="Telefone / WhatsApp" erro={erros.telefone}>
                <input id="telefone" name="telefone" type="tel" className="input" placeholder="+238 …" />
              </Field>
              <Field id="email" label="Email" erro={erros.email} opcional>
                <input id="email" name="email" type="email" className="input" />
              </Field>
            </div>
            <div className="form__row">
              <Field id="nif" label="NIF" erro={erros.nif} opcional>
                <input id="nif" name="nif" className="input" inputMode="numeric" />
              </Field>
              <Field id="data_nascimento" label="Data de nascimento" erro={erros.data_nascimento} opcional>
                <input id="data_nascimento" name="data_nascimento" type="date" className="input" />
              </Field>
            </div>
            <Field id="morada" label="Morada" erro={erros.morada} opcional>
              <input id="morada" name="morada" className="input" />
            </Field>
            <Field id="contacto_emergencia" label="Contacto de emergência" erro={erros.contacto_emergencia} opcional>
              <input id="contacto_emergencia" name="contacto_emergencia" className="input" placeholder="Nome e telefone" />
            </Field>
            <Field id="notas" label="Notas internas" opcional>
              <textarea id="notas" name="notas" className="textarea" style={{ minHeight: 80 }} />
            </Field>
            <label className="check">
              <input type="checkbox" name="consentimento" />
              <span>O sócio autorizou o tratamento dos seus dados pessoais (lei de proteção de dados).</span>
            </label>
            {erros.consentimento && <p className="erro">{erros.consentimento}</p>}
            {erros.detail && <p className="erro">{erros.detail}</p>}
            <div>
              <button className="btn" disabled={aGuardar}>
                {aGuardar ? "A guardar…" : "Guardar sócio"}
              </button>
            </div>
          </div>
        </section>
      </form>
    </>
  );
}
