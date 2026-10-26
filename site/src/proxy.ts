import { NextResponse, type NextRequest } from "next/server";

import { hostDoPedido } from "@/lib/host";

/**
 * Multi-tenant: `ginasio.cv/planos` é servido pela rota interna `/ginasio.cv/planos`.
 * Assim cada domínio tem a sua cache e o mesmo código serve todos os ginásios.
 */
export function proxy(request: NextRequest) {
  const domain = hostDoPedido(request.headers);
  const { pathname, search } = request.nextUrl;
  return NextResponse.rewrite(new URL(`/${domain}${pathname}${search}`, request.url));
}

export const config = {
  matcher: ["/((?!api/|_next/|__nextjs|sw\\.js).*)"],
};
