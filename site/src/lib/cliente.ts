"use client";

import { useCallback, useEffect, useState } from "react";

type Resposta<T> = { ok: boolean; status: number; dados: T | null; erro?: string };

/** Pedido do browser a `/api/<area>/...` (o token vai no cookie httpOnly). */
export async function pedido<T>(
  area: "gestao" | "app",
  caminho: string,
  opcoes: { metodo?: string; corpo?: unknown } = {},
): Promise<Resposta<T>> {
  try {
    const res = await fetch(`/api/${area}/${caminho.replace(/^\//, "")}`, {
      method: opcoes.metodo ?? (opcoes.corpo ? "POST" : "GET"),
      headers: opcoes.corpo ? { "Content-Type": "application/json" } : undefined,
      body: opcoes.corpo ? JSON.stringify(opcoes.corpo) : undefined,
      cache: "no-store",
    });
    const dados = await res.json().catch(() => null);
    if (res.status === 401 && typeof window !== "undefined") {
      window.location.assign(area === "gestao" ? "/gestao/entrar" : "/app/entrar");
    }
    const erro = res.ok ? undefined : primeiroErro(dados);
    return { ok: res.ok, status: res.status, dados: res.ok ? (dados as T) : null, erro };
  } catch {
    return { ok: false, status: 0, dados: null, erro: "Sem ligação à internet." };
  }
}

function primeiroErro(dados: unknown): string {
  if (!dados || typeof dados !== "object") return "Ocorreu um erro. Tente novamente.";
  const d = dados as Record<string, unknown>;
  if (typeof d.detail === "string") return d.detail;
  const primeiro = Object.values(d)[0];
  return Array.isArray(primeiro) ? String(primeiro[0]) : String(primeiro ?? "Ocorreu um erro.");
}

/** Carrega dados do painel e permite recarregar depois de uma ação. */
export function useGestao<T>(caminho: string | null) {
  const [dados, setDados] = useState<T | null>(null);
  const [aCarregar, setACarregar] = useState(true);
  const [erro, setErro] = useState<string>();
  const [versao, setVersao] = useState(0);

  useEffect(() => {
    if (!caminho) return;
    let ativo = true;
    pedido<T>("gestao", caminho).then((r) => {
      if (!ativo) return;
      setDados(r.dados);
      setErro(r.erro);
      setACarregar(false);
    });
    return () => {
      ativo = false;
    };
  }, [caminho, versao]);

  const recarregar = useCallback(() => setVersao((v) => v + 1), []);
  return { dados, aCarregar, erro, recarregar };
}

export function novoId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (c) =>
        (Number(c) ^ (Math.random() * 16) >> (Number(c) / 4)).toString(16),
      );
}
