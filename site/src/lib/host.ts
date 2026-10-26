/** Domínio do visitante → identificador do ginásio usado nas rotas e na API. */
export function normalizarHost(raw: string | null | undefined): string {
  const host = (raw ?? "").split(",")[0].trim().split(":")[0].toLowerCase().replace(/\.$/, "");
  if (!host || host === "localhost" || host === "127.0.0.1") {
    return process.env.DEV_DEFAULT_DOMAIN ?? "forca.localhost";
  }
  return host;
}

export function hostDoPedido(headers: Headers): string {
  return normalizarHost(headers.get("x-forwarded-host") ?? headers.get("host"));
}
