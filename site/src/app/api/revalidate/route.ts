import { revalidateTag } from "next/cache";
import type { NextRequest } from "next/server";

/** Webhook chamado pelo Wagtail ao publicar: revalida só as tags do ginásio afetado. */
export async function POST(request: NextRequest) {
  if (request.headers.get("x-revalidate-secret") !== (process.env.REVALIDATE_SECRET ?? "dev-revalidate-secret")) {
    return Response.json({ ok: false }, { status: 401 });
  }
  const { tags } = (await request.json().catch(() => ({ tags: [] }))) as { tags?: unknown };
  const validas = Array.isArray(tags) ? tags.filter((t): t is string => typeof t === "string").slice(0, 64) : [];
  // expire: 0 → o próximo visitante já vê o conteúdo novo (o gestor quer ver a alteração logo).
  for (const tag of validas) revalidateTag(tag, { expire: 0 });
  return Response.json({ ok: true, revalidadas: validas });
}
