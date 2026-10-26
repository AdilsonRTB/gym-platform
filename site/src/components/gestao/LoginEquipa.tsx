"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { pedido } from "@/lib/cliente";

import { Icon } from "../Icon";

export function LoginEquipa({ nome }: { nome: string }) {
  const router = useRouter();
  const [erro, setErro] = useState<string>();
  const [aEntrar, setAEntrar] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setAEntrar(true);
    const f = new FormData(e.currentTarget);
    const r = await pedido("gestao", "auth/login", { corpo: { email: f.get("email"), password: f.get("password") } });
    if (r.ok) {
      router.replace("/gestao");
      router.refresh();
      return;
    }
    setErro(r.erro);
    setAEntrar(false);
  }

  return (
    <main className="entrar">
      <div className="entrar__cartao">
        <span className="brand">
          <span className="brand__mark" aria-hidden="true">
            {nome.charAt(0)}
          </span>
          {nome}
        </span>
        <h1>Gestão do ginásio</h1>
        <p>Entre com a conta da equipa.</p>
        <form className="form" onSubmit={onSubmit}>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" className="input" autoComplete="username" required autoFocus />
          </div>
          <div className="field">
            <label htmlFor="password">Palavra-passe</label>
            <input id="password" name="password" type="password" className="input" autoComplete="current-password" required />
          </div>
          {erro && (
            <p className="erro" role="alert">
              {erro}
            </p>
          )}
          <button className="btn btn--block" disabled={aEntrar}>
            {aEntrar ? "A entrar…" : "Entrar"}
            {!aEntrar && <Icon name="arrow-right" size={16} />}
          </button>
        </form>
      </div>
    </main>
  );
}
