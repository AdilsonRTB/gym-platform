import type { NextRequest } from "next/server";

import { reencaminhar } from "@/lib/proxyApi";

type Ctx = RouteContext<"/api/gestao/[...path]">;

const handler = async (request: NextRequest, ctx: Ctx) => reencaminhar(request, "gestao", (await ctx.params).path);

export { handler as GET, handler as PATCH, handler as POST };
