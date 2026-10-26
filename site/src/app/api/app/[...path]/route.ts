import type { NextRequest } from "next/server";

import { reencaminhar } from "@/lib/proxyApi";

type Ctx = RouteContext<"/api/app/[...path]">;

const handler = async (request: NextRequest, ctx: Ctx) => reencaminhar(request, "app", (await ctx.params).path);

export { handler as GET, handler as POST };
