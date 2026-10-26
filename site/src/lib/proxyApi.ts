import "server-only";

import type { NextRequest } from "next/server";

import { API_URL } from "./api";
import { hostDoPedido } from "./host";
import { type Area, COOKIE, opcoesCookie } from "./sessao";

/**
 * Reencaminha `/api/<area>/<caminho>` para a API Django com o domínio do ginásio e o token do cookie.
 * `login` guarda o token no cookie; `logout` apaga-o.
 */
export async function reencaminhar(request: NextRequest, area: Area, partes: string[]) {
  const caminho = partes.map(encodeURIComponent).join("/");
  const { nome, prefixo } = COOKIE[area];
  const acao = partes.join("/");
  const ehLogin = (area === "gestao" && acao === "auth/login") || (area === "app" && acao === "auth/entrar");
  const ehLogout = acao === "auth/sair";

  if (ehLogout) {
    return new Response(JSON.stringify({ ok: true }), {
      headers: { "Content-Type": "application/json", "Set-Cookie": `${nome}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax` },
    });
  }

  const token = request.cookies.get(nome)?.value;
  const ip = (request.headers.get("x-forwarded-for") ?? "").split(",")[0].trim();
  const temCorpo = !["GET", "HEAD"].includes(request.method);
  const res = await fetch(`${API_URL}${prefixo}/${caminho}/${request.nextUrl.search}`, {
    method: request.method,
    headers: {
      "Content-Type": "application/json",
      "X-Gym-Host": hostDoPedido(request.headers),
      ...(token && !ehLogin ? { Authorization: `Bearer ${token}` } : {}),
      ...(ip ? { "X-Visitor-Ip": ip } : {}),
    },
    body: temCorpo ? await request.text() : undefined,
    cache: "no-store",
  });
  const texto = await res.text();
  const cabecalhos = new Headers({ "Content-Type": res.headers.get("content-type") ?? "application/json" });

  if (ehLogin && res.ok) {
    const { token: novo, ...resto } = JSON.parse(texto) as { token: string };
    const o = opcoesCookie(area);
    cabecalhos.append(
      "Set-Cookie",
      `${nome}=${novo}; Path=${o.path}; Max-Age=${o.maxAge}; HttpOnly; SameSite=Lax${o.secure ? "; Secure" : ""}`,
    );
    return new Response(JSON.stringify(resto), { status: 200, headers: cabecalhos });
  }
  if (res.status === 401) {
    cabecalhos.append("Set-Cookie", `${nome}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax`);
  }
  return new Response(texto, { status: res.status, headers: cabecalhos });
}
