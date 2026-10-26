"use client";

import { useState } from "react";

import { useRouter } from "next/navigation";

import { pedido } from "@/lib/cliente";

import { Icon } from "../Icon";

/** Entrada sem palavra-passe: código de 6 dígitos por WhatsApp/SMS ou email. */
export function EntrarApp({ nome }: { nome: string }) {
  const router = useRouter();
  const [passo, setPasso] = useState<"contacto" | "codigo">("contacto");
  const [contacto, setContacto] = useState("");
  const [erro, setErro] = useState<string>();
  const [aEnviar, setAEnviar] = useState(false);

  async function pedirCodigo(e: React.FormEvent) {
    e.preventDefault();
    setAEnviar(true);
    setErro(undefined);
    const r = await pedido("app", "auth/codigo", { corpo: { contacto } });
    setAEnviar(false);
    if (r.ok) setPasso("codigo");
    else setErro(r.erro);
  }

  async function entrar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setAEnviar(true);
    setErro(undefined);
    const codigo = new FormData(e.currentTarget).get("codigo");
    const r = await pedido("app", "auth/entrar", { corpo: { contacto, codigo } });
    if (r.ok) {
      router.replace("/app");
        router.refresh();
      return;
    }
    setAEnviar(false);
    setErro(r.erro);
  }

  const email = contacto.includes("@");

  return (
    <main className="entrar">
      <div className="entrar__cartao">
        <span className="brand">
          <span className="brand__mark" aria-hidden="true">
            {nome.charAt(0)}
          </span>
          {nome}
        </span>
        {passo === "contacto" ? (
          <>
            <h1>O seu cartão de sócio, no telemóvel.</h1>
            <p>Indique o telefone ou o email que deu na receção. Enviamos um código de acesso.</p>
            <form className="form" onSubmit={pedirCodigo}>
              <div className="field">
                <label htmlFor="contacto">Telefone ou email</label>
                <input
                  id="contacto"
                  className="input"
                  value={contacto}
                  onChange={(e) => setContacto(e.target.value)}
                  placeholder="+238 … ou nome@email.cv"
                  autoComplete="tel"
                  required
                  autoFocus
                />
              </div>
              {erro && <p className="erro">{erro}</p>}
              <button className="btn btn--block" disabled={aEnviar || contacto.trim().length < 5}>
                {aEnviar ? "A enviar…" : "Receber código"}
                {!aEnviar && <Icon name="arrow-right" size={16} />}
              </button>
            </form>
          </>
        ) : (
          <>
            <h1>Introduza o código</h1>
            <p>
              Se {contacto} estiver registado, enviámos um código de 6 dígitos {email ? "por email" : "por WhatsApp"}.
            </p>
            <form className="form" onSubmit={entrar}>
              <div className="field">
                <label htmlFor="codigo" className="sr-only">
                  Código
                </label>
                <input
                  id="codigo"
                  name="codigo"
                  className="input codigo-input"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="\d{6}"
                  maxLength={6}
                  required
                  autoFocus
                />
              </div>
              {erro && <p className="erro">{erro}</p>}
              <button className="btn btn--block" disabled={aEnviar}>
                {aEnviar ? "A entrar…" : "Entrar"}
              </button>
              <button type="button" className="btn btn--ghost btn--block" onClick={() => setPasso("contacto")}>
                Usar outro contacto
              </button>
            </form>
          </>
        )}
      </div>
    </main>
  );
}
