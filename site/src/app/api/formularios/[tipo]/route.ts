import type { NextRequest } from "next/server";

import { API_URL } from "@/lib/api";
import { hostDoPedido } from "@/lib/host";

const PERMITIDOS = new Set(["leads", "pedidos-dados", "adesoes"]);

/** Reencaminha os formulários do site para a API, com o domínio e o IP do visitante. */
export async function POST(request: NextRequest, ctx: RouteContext<"/api/formularios/[tipo]">) {
  const { tipo } = await ctx.params;
  if (!PERMITIDOS.has(tipo)) return Response.json({ detail: "Não encontrado." }, { status: 404 });

  const ip = (request.headers.get("x-forwarded-for") ?? "").split(",")[0].trim();
  const res = await fetch(`${API_URL}/api/v1/${tipo}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Gym-Host": hostDoPedido(request.headers),
      "User-Agent": request.headers.get("user-agent") ?? "",
      ...(ip ? { "X-Visitor-Ip": ip } : {}),
    },
    body: await request.text(),
    cache: "no-store",
  });
  const corpo = await res.text();
  return new Response(corpo, { status: res.status, headers: { "Content-Type": "application/json" } });
}
