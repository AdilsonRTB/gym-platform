"use client";

/**
 * Check-in tolerante a falhas de rede.
 *
 * - Guarda no dispositivo uma lista mínima de sócios (código, estado, validade), atualizada a cada 5 min.
 * - Sem rede, a entrada é validada com essa lista e fica numa fila local.
 * - Quando a rede volta, a fila é enviada em lote; o servidor ignora duplicados (client_id).
 */

import { novoId, pedido } from "./cliente";

export type SocioOffline = {
  c: string;
  id: number;
  n: number;
  nome: string;
  e: string;
  ate: string | null;
  plano: string | null;
};
type Snapshot = { gerado_em: string; tolerancia: number; socios: SocioOffline[] };
type ItemFila = { client_id: string; codigo?: string; socio_id?: number; momento: string };

export type ResultadoEntrada = {
  permitido: boolean;
  motivo: string;
  offline: boolean;
  socio: { id: number; numero: number; nome: string; plano: string | null; valido_ate: string | null } | null;
};

const K_SNAPSHOT = "gestao:snapshot";
const K_FILA = "gestao:fila";

function ler<T>(chave: string, pordefeito: T): T {
  try {
    const v = localStorage.getItem(chave);
    return v ? (JSON.parse(v) as T) : pordefeito;
  } catch {
    return pordefeito;
  }
}

const EVENTO = "gestao:offline";

function escrever(chave: string, valor: unknown) {
  try {
    localStorage.setItem(chave, JSON.stringify(valor));
    window.dispatchEvent(new Event(EVENTO));
  } catch {
    /* armazenamento cheio ou bloqueado: o check-in online continua a funcionar */
  }
}

/** Para `useSyncExternalStore`: avisa quando a fila ou a lista offline mudam (também noutros separadores). */
export function subscreverOffline(cb: () => void) {
  window.addEventListener(EVENTO, cb);
  window.addEventListener("storage", cb);
  return () => {
    window.removeEventListener(EVENTO, cb);
    window.removeEventListener("storage", cb);
  };
}

export const snapshot = () => ler<Snapshot | null>(K_SNAPSHOT, null);
export const fila = () => ler<ItemFila[]>(K_FILA, []);

export async function atualizarSnapshot(): Promise<boolean> {
  const r = await pedido<Snapshot>("gestao", "checkins/snapshot");
  if (r.ok && r.dados) escrever(K_SNAPSHOT, r.dados);
  return r.ok;
}

function hojeCV(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Atlantic/Cape_Verde" }).format(new Date());
}

function validarLocal(s: SocioOffline | undefined, tolerancia: number): { permitido: boolean; motivo: string } {
  if (!s) return { permitido: false, motivo: "Cartão desconhecido" };
  if (s.e === "suspenso") return { permitido: false, motivo: "Sócio suspenso" };
  if (!s.ate) return { permitido: false, motivo: "Sem assinatura ativa" };
  const hoje = hojeCV();
  if (s.ate >= hoje) return { permitido: true, motivo: "Assinatura válida" };
  const limite = new Date(`${s.ate}T12:00:00`);
  limite.setDate(limite.getDate() + tolerancia);
  return limite.toISOString().slice(0, 10) >= hoje
    ? { permitido: true, motivo: "Mensalidade em atraso (dentro da tolerância)" }
    : { permitido: false, motivo: "Mensalidade em atraso" };
}

/** Regista uma entrada: online se possível, senão valida localmente e guarda na fila. */
export async function registarEntrada(alvo: { codigo?: string; socio_id?: number }): Promise<ResultadoEntrada> {
  const item: ItemFila = { ...alvo, client_id: novoId(), momento: new Date().toISOString() };

  if (typeof navigator === "undefined" || navigator.onLine) {
    const r = await pedido<Omit<ResultadoEntrada, "offline">>("gestao", "checkins", {
      corpo: { ...item, dispositivo: navigator.userAgent.slice(0, 80) },
    });
    if (r.ok && r.dados) return { ...r.dados, offline: false };
    if (r.status !== 0) return { permitido: false, motivo: r.erro ?? "Erro", offline: false, socio: null };
  }

  const snap = snapshot();
  const s = snap?.socios.find((x) => (alvo.codigo ? x.c === alvo.codigo.trim() : x.id === alvo.socio_id));
  const { permitido, motivo } = validarLocal(s, snap?.tolerancia ?? 0);
  escrever(K_FILA, [...fila(), item]);
  return {
    permitido,
    motivo: snap ? motivo : "Sem lista offline: entrada registada para validação",
    offline: true,
    socio: s ? { id: s.id, numero: s.n, nome: s.nome, plano: s.plano, valido_ate: s.ate } : null,
  };
}

/** Envia a fila offline. Devolve quantas entradas foram sincronizadas. */
export async function sincronizar(): Promise<number> {
  const pendentes = fila();
  if (pendentes.length === 0) return 0;
  const r = await pedido<{ resultados: { client_id: string; erro?: unknown }[] }>("gestao", "checkins/lote", {
    corpo: { itens: pendentes },
  });
  if (!r.ok || !r.dados) return 0;
  const tratados = new Set(r.dados.resultados.map((x) => x.client_id));
  escrever(
    K_FILA,
    fila().filter((i) => !tratados.has(i.client_id)),
  );
  return tratados.size;
}

export function procurarLocal(termo: string): SocioOffline[] {
  const t = termo.trim().toLowerCase();
  if (t.length < 2) return [];
  const numero = Number(t);
  return (snapshot()?.socios ?? [])
    .filter((s) => (Number.isFinite(numero) && s.n === numero) || s.nome.toLowerCase().includes(t))
    .slice(0, 6);
}
