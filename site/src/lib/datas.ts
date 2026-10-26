const TZ = "Atlantic/Cape_Verde";

/** "2026-09-25" ou ISO → "25 set" / "25/09/2026". */
export function dataCurta(valor: string | null | undefined): string {
  if (!valor) return "—";
  const d = new Date(valor.length === 10 ? `${valor}T12:00:00` : valor);
  return new Intl.DateTimeFormat("pt-PT", { day: "numeric", month: "short", timeZone: TZ }).format(d).replace(".", "");
}

export function dataLonga(valor: string | null | undefined): string {
  if (!valor) return "—";
  const d = new Date(valor.length === 10 ? `${valor}T12:00:00` : valor);
  return new Intl.DateTimeFormat("pt-PT", { day: "2-digit", month: "2-digit", year: "numeric", timeZone: TZ }).format(d);
}

export function hora(valor: string): string {
  return new Intl.DateTimeFormat("pt-PT", { hour: "2-digit", minute: "2-digit", timeZone: TZ }).format(new Date(valor));
}

export function quando(valor: string): string {
  const d = new Date(valor);
  const hoje = new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(new Date());
  const dia = new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(d);
  return dia === hoje ? `Hoje, ${hora(valor)}` : `${dataCurta(valor)}, ${hora(valor)}`;
}

export function diasAte(data: string): number {
  const hoje = new Date(`${new Intl.DateTimeFormat("en-CA", { timeZone: TZ }).format(new Date())}T12:00:00`);
  return Math.round((new Date(`${data}T12:00:00`).getTime() - hoje.getTime()) / 86400000);
}
