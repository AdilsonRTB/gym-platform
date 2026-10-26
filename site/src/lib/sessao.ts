import "server-only";

import { cookies } from "next/headers";

import { API_URL } from "./api";

/** Cookies httpOnly com os tokens da API (o JavaScript do browser nunca os vê). */
export const COOKIE = {
  gestao: { nome: "gestao_sessao", maxAge: 60 * 60 * 12, prefixo: "/api/v1/gestao" },
  app: { nome: "app_sessao", maxAge: 60 * 60 * 24 * 60, prefixo: "/api/v1/socio" },
} as const;

export type Area = keyof typeof COOKIE;

export const opcoesCookie = (area: Area) => ({
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
  maxAge: COOKIE[area].maxAge,
});

export async function tokenDe(area: Area): Promise<string | undefined> {
  return (await cookies()).get(COOKIE[area].nome)?.value;
}

/** Pedido autenticado à API a partir de um Server Component (sem cache: dados privados). */
export async function apiPrivada<T>(area: Area, domain: string, path: string): Promise<{ status: number; dados: T | null }> {
  const token = await tokenDe(area);
  if (!token) return { status: 401, dados: null };
  const res = await fetch(`${API_URL}${COOKIE[area].prefixo}${path}`, {
    headers: { "X-Gym-Host": domain, Authorization: `Bearer ${token}`, Accept: "application/json" },
    cache: "no-store",
  });
  return { status: res.status, dados: res.ok ? ((await res.json()) as T) : null };
}
