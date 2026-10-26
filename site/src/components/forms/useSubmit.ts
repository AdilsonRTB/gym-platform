"use client";

import { useState } from "react";

export type Erros = Record<string, string>;

/** Envia um formulário para /api/formularios/<tipo> e traduz os erros de validação da API. */
export function useSubmit<T = unknown>(tipo: string) {
  const [aEnviar, setAEnviar] = useState(false);
  const [erros, setErros] = useState<Erros>({});

  async function enviar(dados: Record<string, unknown>): Promise<T | null> {
    setAEnviar(true);
    setErros({});
    try {
      const res = await fetch(`/api/formularios/${tipo}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      });
      const corpo = await res.json().catch(() => ({}));
      if (res.ok) return corpo as T;
      if (res.status === 429) {
        setErros({ geral: "Demasiados pedidos. Tente novamente dentro de um minuto." });
      } else {
        const e: Erros = {};
        for (const [k, v] of Object.entries(corpo ?? {})) {
          e[k === "detail" || k === "non_field_errors" ? "geral" : k] = Array.isArray(v) ? String(v[0]) : String(v);
        }
        setErros(Object.keys(e).length ? e : { geral: "Não foi possível enviar. Tente novamente." });
      }
      return null;
    } catch {
      setErros({ geral: "Sem ligação. Verifique a internet e tente novamente." });
      return null;
    } finally {
      setAEnviar(false);
    }
  }

  return { enviar, aEnviar, erros };
}
