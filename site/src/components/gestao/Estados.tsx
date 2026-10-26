import type { Cobranca, SocioResumo } from "@/lib/gestaoTypes";

export function EstadoSocio({ s }: { s: Pick<SocioResumo, "estado" | "assinatura" | "em_atraso"> }) {
  if (s.estado === "suspenso") return <span className="estado estado--erro">Suspenso</span>;
  if (s.estado === "inativo") return <span className="estado">Inativo</span>;
  if (!s.assinatura) return <span className="estado estado--aviso">Sem plano</span>;
  if (s.em_atraso || !s.assinatura.valida) return <span className="estado estado--erro">Em atraso</span>;
  if (s.assinatura.dias_restantes <= 5) return <span className="estado estado--aviso">A renovar</span>;
  return <span className="estado estado--ok">Ativo</span>;
}

export function EstadoCobranca({ c }: { c: Pick<Cobranca, "estado" | "atrasada"> }) {
  if (c.estado === "paga") return <span className="estado estado--ok">Paga</span>;
  if (c.estado === "anulada") return <span className="estado">Anulada</span>;
  if (c.atrasada) return <span className="estado estado--erro">Em atraso</span>;
  return <span className="estado estado--aviso">Por pagar</span>;
}
