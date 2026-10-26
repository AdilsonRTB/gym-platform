const cve = new Intl.NumberFormat("pt-CV", { maximumFractionDigits: 0 });

/** 3500 → "3 500" (o sufixo CVE é mostrado à parte). */
export const formatarCve = (valor: number) => cve.format(valor).replace(/ | |,/g, " ");

export const PERIODICIDADE: Record<string, string> = {
  avulso: "por aula",
  semanal: "/semana",
  mensal: "/mês",
  trimestral: "/trimestre",
  semestral: "/semestre",
  anual: "/ano",
};

export const NIVEL: Record<string, string> = {
  todos: "Todos os níveis",
  iniciante: "Iniciante",
  intermedio: "Intermédio",
  avancado: "Avançado",
};

export const DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
export const DIAS_CURTOS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

/** Dia da semana em Cabo Verde (0 = segunda). */
export function diaDeHoje(): number {
  const nome = new Intl.DateTimeFormat("en-US", { weekday: "short", timeZone: "Atlantic/Cape_Verde" }).format(
    new Date(),
  );
  return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(nome);
}

export function iniciais(nome: string): string {
  const partes = nome.trim().split(/\s+/);
  return ((partes[0]?.[0] ?? "") + (partes.length > 1 ? partes[partes.length - 1][0] : "")).toUpperCase();
}

/** Links do CMS: caminhos internos ou URLs completos. */
export function isExterno(link: string) {
  return /^https?:\/\//.test(link) || link.startsWith("mailto:") || link.startsWith("tel:");
}

export function whatsappUrl(numero: string, texto = "") {
  const digitos = numero.replace(/\D/g, "");
  return `https://wa.me/${digitos}${texto ? `?text=${encodeURIComponent(texto)}` : ""}`;
}
