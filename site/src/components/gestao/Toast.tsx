"use client";

import { useCallback, useEffect, useState } from "react";

/** Mensagem curta de confirmação no fundo do ecrã. */
export function useToast() {
  const [mensagem, setMensagem] = useState<string | null>(null);
  useEffect(() => {
    if (!mensagem) return;
    const t = setTimeout(() => setMensagem(null), 3200);
    return () => clearTimeout(t);
  }, [mensagem]);
  const mostrar = useCallback((m: string) => setMensagem(m), []);
  const toast = mensagem ? (
    <div className="toast" role="status">
      {mensagem}
    </div>
  ) : null;
  return { mostrar, toast };
}
